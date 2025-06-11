from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import logging
from vector_store import FaissVectorStore
from document_processor import DocumentProcessor, DocumentChunk
from typing import List, Dict, Any
from werkzeug.utils import secure_filename
import traceback
from pathlib import Path
from loguru import logger
import json
from models import db, User, SystemConfig
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredPDFLoader, TextLoader
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化知识库目录
KNOWLEDGE_BASE_DIR = Path("knowledge_base")
VECTOR_STORE_PATH = KNOWLEDGE_BASE_DIR / "vector_store"

# 确保知识库目录存在
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

# 初始化向量存储
vector_store = None
try:
    logger.info("初始化向量存储...")
    vector_store = FaissVectorStore()
    
    # 尝试加载现有的向量存储
    if VECTOR_STORE_PATH.with_suffix('.index').exists():
        logger.info("加载现有向量存储...")
        vector_store.load(str(VECTOR_STORE_PATH))
    else:
        logger.info("未找到现有向量存储，创建新的实例")
except Exception as e:
    logger.error(f"初始化向量存储失败: {str(e)}")
    logger.error(traceback.format_exc())
    raise

def save_vector_store():
    """保存向量存储到文件"""
    if not vector_store:
        logger.error("向量存储未初始化，无法保存")
        return
        
    try:
        store_file = str(VECTOR_STORE_PATH)
        logger.info(f"正在保存向量存储到 {store_file}...")
        vector_store.save(store_file)
        logger.info("向量存储保存成功")
    except Exception as e:
        logger.error(f"保存向量存储失败: {str(e)}")
        logger.error(traceback.format_exc())

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = 'uploads'  # 上传文件保存目录
app.config['SECRET_KEY'] = 'your-secret-key'  # 用于session加密
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

# 确保上传目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    # Microsoft Office
    'doc', 'docx',  # Word
    'xls', 'xlsx',  # Excel
    'ppt', 'pptx',  # PowerPoint
    # PDF
    'pdf',
    # 文本文件
    'txt', 'md', 'csv', 'json'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_type_dir(file_type: str) -> str:
    """根据文件类型返回对应的目录名"""
    type_mapping = {
        # Microsoft Office
        'doc': 'word',
        'docx': 'word',
        'xls': 'excel',
        'xlsx': 'excel',
        'ppt': 'powerpoint',
        'pptx': 'powerpoint',
        # PDF
        'pdf': 'pdf',
        # 文本文件
        'txt': 'text',
        'md': 'text',
        'csv': 'text',
        'json': 'text'
    }
    return type_mapping.get(file_type, 'other')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_document_info(file_path: Path) -> dict:
    """获取文档信息"""
    try:
        # 获取文件基本信息
        stat = file_path.stat()
        size_kb = stat.st_size / 1024
        size_str = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{(size_kb/1024):.1f}MB"
        
        stats = {
            'size': size_str,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'type': file_path.suffix.lstrip('.').upper(),
            'chunks': 0  # 默认值
        }
        
        # 获取文档在向量存储中的信息
        try:
            if vector_store:
                doc_stats = vector_store.get_document_stats(str(file_path))
                if doc_stats and isinstance(doc_stats, dict):
                    stats.update({
                        'chunks': doc_stats.get('chunks', 0)
                    })
        except Exception as ve:
            logger.error(f"获取文档向量信息失败 {file_path}: {str(ve)}")
        
        return stats
    except Exception as e:
        logger.error(f"获取文档信息失败 {file_path}: {str(e)}")
        return {
            'size': '0KB',
            'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': file_path.suffix.lstrip('.').upper(),
            'chunks': 0
        }

def get_knowledge_base_info():
    """获取知识库统计信息"""
    try:
        if not vector_store:
            logger.warning("向量存储未初始化")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'vector_dimension': 0
            }
            
        # 获取向量存储的统计信息
        stats = vector_store.get_statistics()
        if not stats:
            logger.warning("无法获取向量存储统计信息")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'vector_dimension': 0
            }
            
        # 获取上传目录中的实际文件数量
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        actual_files = []
        for type_dir in upload_dir.glob('*'):
            if type_dir.is_dir():
                for file_path in type_dir.glob('*'):
                    if file_path.is_file() and file_path.suffix.lstrip('.').lower() in ALLOWED_EXTENSIONS:
                        actual_files.append(file_path)
        
        return {
            'total_documents': len(actual_files),  # 使用实际文件数量
            'total_chunks': stats.get('total_chunks', 0),
            'vector_dimension': stats.get('vector_dimension', 0)
        }
    except Exception as e:
        logger.error(f"获取知识库信息失败: {str(e)}")
        return {
            'total_documents': 0,
            'total_chunks': 0,
            'vector_dimension': 0
        }

@app.route('/api/documents', methods=['GET'])
@login_required
def get_documents():
    """获取文档列表"""
    try:
        documents = []
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        
        # 遍历所有文档类型目录
        for type_dir in upload_dir.glob('*'):
            if type_dir.is_dir():
                # 遍历目录下的所有文件
                for file_path in type_dir.glob('*'):
                    if file_path.is_file() and file_path.suffix.lstrip('.').lower() in ALLOWED_EXTENSIONS:
                        try:
                            doc_info = get_document_info(file_path)
                            documents.append({
                                'id': len(documents) + 1,
                                'name': file_path.name,
                                'path': str(file_path),
                                'type': doc_info['type'],
                                'size': doc_info['size'],
                                'chunks': doc_info.get('chunks', 0),
                                'modified': doc_info['modified']
                            })
                            logger.debug(f"添加文档到列表: {file_path.name}, 信息: {doc_info}")
                        except Exception as e:
                            logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
                            continue
        
        # 按修改时间降序排序
        documents.sort(key=lambda x: x['modified'], reverse=True)
        
        logger.info(f"获取到 {len(documents)} 个文档")
        return jsonify(documents)
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    """删除文档"""
    try:
        # 获取文档列表
        documents = []
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        
        for type_dir in upload_dir.glob('*'):
            if type_dir.is_dir():
                for file_path in type_dir.glob('*'):
                    if file_path.is_file() and file_path.suffix.lstrip('.').lower() in ALLOWED_EXTENSIONS:
                        documents.append(file_path)
        
        if 0 <= doc_id - 1 < len(documents):
            file_path = documents[doc_id - 1]
            
            # 从向量存储中删除
            vector_store.delete_document(str(file_path))
            
            # 删除文件
            file_path.unlink()
            
            # 如果目录为空，删除目录
            if not any(file_path.parent.iterdir()):
                file_path.parent.rmdir()
                
            return jsonify({'success': True})
        else:
            return jsonify({'error': '文档不存在'}), 404
            
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
            
        flash('用户名或密码错误', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    try:
        if not vector_store:
            raise Exception("向量存储未初始化")
            
        # 获取统计信息
        stats = vector_store.get_statistics()
        
        # 获取支持的文件格式
        formats = ', '.join(sorted(list(ALLOWED_EXTENSIONS)))
        
        return render_template('index.html', 
                             total_documents=stats['total_documents'],
                             total_chunks=stats['total_chunks'],
                             vector_dimension=stats['vector_dimension'],
                             supported_formats=formats)
    except Exception as e:
        logger.error(f"渲染首页失败: {str(e)}")
        logger.error(traceback.format_exc())
        # 返回带有错误信息的模板
        formats = ', '.join(sorted(list(ALLOWED_EXTENSIONS)))
        return render_template('index.html',
                             error_message=str(e),
                             total_documents="0",
                             total_chunks="0",
                             vector_dimension="0",
                             supported_formats=formats)

@app.route('/api/stats')
@login_required
def get_stats():
    try:
        stats = vector_store.get_statistics()
        return jsonify({
            'total_documents': stats['total_documents'],
            'total_chunks': stats['total_chunks'],
            'vector_dimension': stats['vector_dimension']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['POST'])
@login_required
def add_document():
    if not current_user.can_upload:
        return jsonify({'error': '您没有上传权限'}), 403
        
    try:
        content = request.json.get('content')
        if not content:
            return jsonify({'error': '文档内容不能为空'}), 400
        
        # 添加文档到知识库
        vector_store.add_document(content)
        
        # 保存向量存储
        save_vector_store()
        
        return jsonify({'message': '文档添加成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
@login_required
def search():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': '缺少查询参数'}), 400
            
        query = data['query']
        logger.info("接收到搜索请求")
        logger.info(f"开始搜索查询: {query}")
        
        # 增加返回结果数量到10个
        results = vector_store.search(query, top_k=10)  # 增加返回结果数量
        
        if not results:
            return jsonify({
                'message': '没有找到相关内容',
                'results': []
            }), 200
            
        # 处理搜索结果
        formatted_results = []
        for text, score, metadata in results:
            formatted_results.append({
                'content': text,
                'score': float(score),  # 确保score是可序列化的
                'metadata': metadata
            })
            
        return jsonify({
            'message': '搜索成功',
            'results': formatted_results
        }), 200
        
    except Exception as e:
        logger.error(f"搜索时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def calculate_relevance_score(query, text):
    """
    计算文本与查询的相关性得分
    """
    try:
        # 对查询和文本进行分词
        import jieba
        query_words = list(jieba.cut(query))
        text_words = list(jieba.cut(text))
        
        # 计算查询词在文本中的出现次数
        word_counts = {}
        total_matches = 0
        for word in query_words:
            count = text_words.count(word)
            word_counts[word] = count
            total_matches += count
        
        # 计算相关性得分
        if not query_words:
            return 0
            
        # 基础分数：匹配词数量 / 查询词数量
        base_score = len([w for w in query_words if w in text_words]) / len(query_words)
        
        # 密度分数：考虑匹配词的密集程度
        density_score = 0
        if total_matches > 0:
            # 找到第一个和最后一个匹配词的位置
            first_pos = float('inf')
            last_pos = -1
            for i, word in enumerate(text_words):
                if word in query_words:
                    first_pos = min(first_pos, i)
                    last_pos = max(last_pos, i)
            
            if first_pos != float('inf'):
                # 计算匹配词的密集程度
                span = last_pos - first_pos + 1
                density_score = total_matches / span if span > 0 else 0
        
        # 组合得分
        relevance_score = (base_score + density_score) / 2
        
        logger.debug(f"相关性得分 - 基础分数: {base_score}, 密度分数: {density_score}, 最终得分: {relevance_score}")
        logger.debug(f"词频统计: {word_counts}")
        
        return relevance_score
        
    except Exception as e:
        logger.error(f"计算相关性得分失败: {str(e)}")
        return 0

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        # 检查是否有文件
        if 'files[]' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
            
        files = request.files.getlist('files[]')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': '没有选择文件'}), 400
            
        results = []
        for file in files:
            filename = secure_filename(file.filename)
            if not filename or not allowed_file(filename):
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': '不支持的文件类型'
                })
                continue
                
            # 获取文件扩展名
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 根据文件类型创建子目录
            type_dir = get_type_dir(file_ext.lstrip('.'))
            save_dir = Path(app.config['UPLOAD_FOLDER']) / type_dir
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            file_path = save_dir / filename
            file.save(str(file_path))
            
            # 处理文档
            try:
                # 根据文件类型选择处理方法
                if file_ext in ['.xlsx', '.xls']:
                    # 处理Excel文件
                    try:
                        # 读取所有sheet
                        dfs = pd.read_excel(str(file_path), sheet_name=None)
                        text_contents = []
                        metadata_list = []
                        
                        # 处理每个sheet
                        for sheet_name, df in dfs.items():
                            # 将sheet名称添加为标题
                            sheet_text = f"Sheet: {sheet_name}\n\n"
                            
                            # 添加列名
                            sheet_text += "列: " + ", ".join(df.columns) + "\n\n"
                            
                            # 将数据转换为文本
                            for idx, row in df.iterrows():
                                row_text = " | ".join([f"{col}: {str(val)}" for col, val in row.items()])
                                text_contents.append(row_text)
                                metadata_list.append({
                                    'source': str(file_path),
                                    'sheet': sheet_name,
                                    'row': idx + 1
                                })
                            
                            # 添加sheet概述
                            text_contents.append(sheet_text)
                            metadata_list.append({
                                'source': str(file_path),
                                'sheet': sheet_name,
                                'type': 'summary'
                            })
                        
                        # 添加到向量存储
                        if vector_store.add(text_contents, metadata_list):
                            # 保存向量存储
                            save_vector_store()
                            results.append({
                                'filename': filename,
                                'success': True,
                                'error': None
                            })
                        else:
                            raise Exception('添加到向量库失败')
                            
                    except Exception as e:
                        logger.error(f"处理Excel文件失败: {str(e)}")
                        file_path.unlink()
                        results.append({
                            'filename': filename,
                            'success': False,
                            'error': f'处理Excel文件失败: {str(e)}'
                        })
                        continue
                        
                elif file_ext == '.pdf':
                    loader = UnstructuredPDFLoader(str(file_path))
                    documents = loader.load()
                else:
                    loader = TextLoader(str(file_path), encoding='utf-8')
                    documents = loader.load()
                    
                # 处理PDF和文本文件
                if file_ext != '.xlsx' and file_ext != '.xls':
                    # 分割文本
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=500,
                        chunk_overlap=50,
                        length_function=len,
                        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
                    )
                    texts = text_splitter.split_documents(documents)
                    
                    # 获取文本内容和元数据
                    text_contents = []
                    metadata_list = []
                    for doc in texts:
                        text_contents.append(doc.page_content)
                        metadata_list.append({'source': str(file_path)})
                    
                    # 添加到向量存储
                    if vector_store.add(text_contents, metadata_list):
                        # 保存向量存储
                        save_vector_store()
                        results.append({
                            'filename': filename,
                            'success': True,
                            'error': None
                        })
                    else:
                        raise Exception('添加到向量库失败')
                
            except Exception as e:
                logger.error(f"处理文档失败: {str(e)}")
                # 如果处理失败，删除上传的文件
                file_path.unlink()
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': f'处理文档失败: {str(e)}'
                })
                
        return jsonify({
            'results': results,
            'info': get_knowledge_base_info()
        })
        
    except Exception as e:
        logger.error(f"上传处理失败: {str(e)}")
        return jsonify({'error': f'上传处理失败: {str(e)}'}), 500

# 用户管理路由
@app.route('/user-management')
@login_required
def user_management():
    if not current_user.is_admin:
        flash('您没有访问此页面的权限', 'danger')
        return redirect(url_for('index'))
    return render_template('user_management.html')

# 权限管理路由
@app.route('/permission-management')
@login_required
def permission_management():
    if not current_user.is_admin:
        flash('您没有访问此页面的权限', 'danger')
        return redirect(url_for('index'))
    return render_template('permission_management.html')

# API路由
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if not current_user.is_admin:
        return jsonify({'error': '没有权限'}), 403
    # 排除 admin 用户
    users = User.query.filter(User.username != 'admin').all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'can_upload': user.can_upload,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    } for user in users])

@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': '没有权限'}), 403
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'can_upload': user.can_upload
        })
        
    elif request.method == 'PUT':
        data = request.get_json()
        
        if 'email' in data:
            user.email = data['email']
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        if 'is_admin' in data and user.username != 'admin':
            user.is_admin = data['is_admin']
        if 'can_upload' in data and user.username != 'admin':
            user.can_upload = data['can_upload']
            
        db.session.commit()
        return jsonify({'message': '用户信息已更新'})
        
    elif request.method == 'DELETE':
        if user.username == 'admin':
            return jsonify({'error': '不能删除管理员账户'}), 400
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': '用户已删除'})

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        return jsonify({'error': '没有权限'}), 403
        
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'error': '缺少必要的字段'}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 400
        
    user = User(
        username=data['username'],
        email=data.get('email'),
        is_admin=data.get('is_admin', False),
        can_upload=data.get('can_upload', True)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '用户创建成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'can_upload': user.can_upload
        }
    })

def init_db():
    """Initialize the database and create admin user"""
    with app.app_context():
        db.create_all()
        
        # Set admin credentials in system config if not exists
        if not SystemConfig.get_value('ADMIN_PASSWORD'):
            SystemConfig.set_value('ADMIN_USERNAME', 'admin', 'Default admin username')
            SystemConfig.set_value('ADMIN_PASSWORD', 'Password1', 'Default admin password')
            SystemConfig.set_value('ADMIN_EMAIL', 'admin@example.com', 'Default admin email')
            print("Admin credentials initialized in database")
        
        # Initialize admin user
        User.init_admin()

if __name__ == '__main__':
    init_db()  # Initialize database and admin user
    app.run(debug=True, host='0.0.0.0', port=5000) 