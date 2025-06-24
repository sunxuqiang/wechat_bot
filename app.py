print('主程序入口:', __file__)
import document_processor
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
from config_loader import config
import signal
import sys
from file_processors.processor_factory import ProcessorFactory
from knowledge_query_service import get_knowledge_query_service

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化知识库查询服务
knowledge_query_service = get_knowledge_query_service()

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
        
    # 设置向量存储到知识库查询服务
    knowledge_query_service.set_vector_store(vector_store)
    logger.info("知识库查询服务已设置向量存储")
    
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
app.config['MAX_CONTENT_LENGTH'] = config.getint('server', 'max_content_length')  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = config.get('paths', 'upload_folder')  # 上传文件保存目录
app.config['SECRET_KEY'] = config.get('server', 'secret_key')  # 用于session加密
app.config['SQLALCHEMY_DATABASE_URI'] = config.get('database', 'sqlalchemy_database_uri')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.getboolean('database', 'sqlalchemy_track_modifications')

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
        
        # 获取文档在向量存储中的信息
        chunks = 0
        try:
            if vector_store:
                doc_stats = vector_store.get_document_stats(str(file_path))
                if doc_stats and isinstance(doc_stats, dict):
                    chunks = doc_stats.get('chunks', 0)
        except Exception as ve:
            logger.error(f"获取文档向量信息失败 {file_path}: {str(ve)}")
        
        return {
            'size': size_str,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'type': file_path.suffix.lstrip('.').upper(),
            'chunks': chunks
        }
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
                'vector_dimension': 0,
                'documents': []
            }
            
        # 获取文档列表和统计信息
        documents = []
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        
        # 遍历所有文档类型目录
        for type_dir in upload_dir.glob('*'):
            if type_dir.is_dir():
                for file_path in type_dir.glob('*'):
                    if file_path.is_file() and file_path.suffix.lstrip('.').lower() in ALLOWED_EXTENSIONS:
                        try:
                            # 获取文档信息
                            doc_info = get_document_info(file_path)
                            doc = {
                                'id': len(documents) + 1,
                                'name': file_path.name,
                                'path': str(file_path),
                                'type': doc_info['type'],
                                'size': doc_info['size'],
                                'chunks': doc_info.get('chunks', 0),
                                'modified': doc_info['modified']
                            }
                            documents.append(doc)
                        except Exception as e:
                            logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
                            continue
        
        # 按修改时间降序排序
        documents.sort(key=lambda x: x['modified'], reverse=True)
        
        # 获取向量存储的维度信息
        vector_dimension = 0
        if vector_store and vector_store.model:
            vector_dimension = vector_store.model.get_sentence_embedding_dimension()
        
        # 使用 vector_store.documents 的长度作为文本块总数
        total_chunks = len(vector_store.documents) if vector_store and hasattr(vector_store, 'documents') else 0
        
        # 使用向量存储中的文档数量作为总文档数（而不是上传目录的文件数）
        # 统计向量存储中不同源文件的数量
        total_documents = 0
        if vector_store and hasattr(vector_store, 'documents') and vector_store.documents:
            unique_sources = set()
            for _, metadata in vector_store.documents:
                if 'source' in metadata:
                    unique_sources.add(metadata['source'])
            total_documents = len(unique_sources)
        
        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'vector_dimension': vector_dimension,
            'documents': documents
        }
    except Exception as e:
        logger.error(f"获取知识库信息失败: {str(e)}")
        return {
            'total_documents': 0,
            'total_chunks': 0,
            'vector_dimension': 0,
            'documents': []
        }

@app.route('/api/documents', methods=['GET'])
@login_required
def get_documents():
    """获取文档列表"""
    try:
        info = get_knowledge_base_info()
        return jsonify(info['documents'])
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
            
            # 保存向量存储的更改
            save_vector_store()
            
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
        try:
            # 处理JSON数据
            if request.is_json:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                remember = data.get('remember', False)
            # 处理表单数据
            else:
                username = request.form.get('username')
                password = request.form.get('password')
                remember = request.form.get('remember', False)
            
            if not username or not password:
                if request.is_json:
                    return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
                flash('用户名和密码不能为空', 'danger')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                if request.is_json:
                    return jsonify({'success': True, 'message': '登录成功'})
                    
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('index')
                return redirect(next_page)
            
            if request.is_json:
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            flash('用户名或密码错误', 'danger')
            
        except Exception as e:
            logger.error(f"登录过程发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            if request.is_json:
                return jsonify({'success': False, 'message': '服务器错误，请稍后重试'}), 500
            flash('服务器错误，请稍后重试', 'danger')
            
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
            
        # 获取知识库信息
        info = get_knowledge_base_info()
        
        # 获取支持的文件格式
        formats = ', '.join(sorted(list(ALLOWED_EXTENSIONS)))
        
        return render_template('index.html', 
                             total_documents=info['total_documents'],
                             total_chunks=info['total_chunks'],
                             vector_dimension=info['vector_dimension'],
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
        info = get_knowledge_base_info()
        return jsonify({
            'total_documents': info['total_documents'],
            'total_chunks': info['total_chunks'],
            'vector_dimension': info['vector_dimension']
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
        
        # 使用知识库查询服务的Web专用搜索方法
        search_result = knowledge_query_service.search_for_web(
            query=query, 
            include_metadata=True
        )
        
        if not search_result['success']:
            return jsonify({
                'error': search_result['error'],
                'results': []
            }), 400
        
        if not search_result['results']:
            return jsonify({
                'message': search_result['message'],
                'results': []
            }), 200
        
        # 格式化结果为API响应格式
        formatted_results = knowledge_query_service.format_results_for_api(search_result['results'])
        
        return jsonify({
            'message': search_result['message'],
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
                # 使用新的文件处理器系统
                processor_factory = ProcessorFactory()
                processor = processor_factory.get_processor(str(file_path))
                
                if not processor:
                    raise Exception(f'不支持的文件类型: {file_ext}')
                
                # 处理文件
                chunks = processor.process(str(file_path))
                if not chunks:
                    raise Exception('文件处理失败，没有生成文本块')
                
                # 提取文本和元数据
                text_contents = [chunk["text"] for chunk in chunks]
                metadata_list = [chunk["metadata"] for chunk in chunks]
                
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

@app.route('/permission_management')
@login_required
def permission_management():
    """权限管理页面"""
    return render_template('permission_management.html')

@app.route('/text-blocks')
@login_required
def text_blocks_page():
    """文本块查询页面"""
    return render_template('text_blocks.html')

@app.route('/api/text_blocks')
@login_required
def get_text_blocks():
    """获取文本块列表"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        search = request.args.get('search', '')

        if not vector_store:
            logger.error("向量存储未初始化")
            return jsonify({
                'success': False,
                'message': '向量存储未初始化'
            }), 500

        if not hasattr(vector_store, 'documents') or not vector_store.documents:
            logger.warning("向量存储中没有文档")
            return jsonify({
                'success': True,
                'text_blocks': [],
                'total': 0,
                'total_pages': 0
            })

        # 获取所有文本块
        all_blocks = []
        for i, (content, metadata) in enumerate(vector_store.documents):
            try:
                if search and search.lower() not in content.lower():
                    continue
                all_blocks.append({
                    'id': i + 1,
                    'content': content,
                    'source': metadata.get('source', '未知'),
                    'create_time': metadata.get('created_at', '未知')
                })
            except Exception as e:
                logger.error(f"处理文档时出错: {str(e)}")
                continue

        # 计算分页
        total = len(all_blocks)
        start = (page - 1) * size
        end = start + size
        items = all_blocks[start:end]

        logger.info(f"成功获取文本块列表: 总数={total}, 当前页={page}, 每页大小={size}")
        return jsonify({
            'success': True,
            'text_blocks': items,
            'total': total,
            'total_pages': (total + size - 1) // size
        })
    except Exception as e:
        logger.error(f"获取文本块列表失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/text_blocks/<int:block_id>')
@login_required
def get_text_block(block_id):
    """获取单个文本块详情"""
    try:
        if not vector_store:
            return jsonify({'success': False, 'message': '向量存储未初始化'}), 500

        # 获取所有文本块
        all_blocks = []
        for i, (content, metadata) in enumerate(vector_store.documents):
            all_blocks.append({
                'id': i + 1,
                'content': content,
                'source': metadata.get('source', '未知'),
                'create_time': metadata.get('created_at', '未知')
            })

        if 0 <= block_id - 1 < len(all_blocks):
            return jsonify({
                'success': True,
                'text_block': all_blocks[block_id - 1]
            })
        else:
            return jsonify({'success': False, 'message': '文本块不存在'}), 404
    except Exception as e:
        logger.error(f"获取文本块详情失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/text_blocks/<int:block_id>', methods=['DELETE'])
@login_required
def delete_text_block(block_id):
    """删除单个文本块"""
    try:
        if not vector_store:
            return jsonify({'success': False, 'message': '向量存储未初始化'}), 500

        # 验证索引范围（block_id从1开始，需要转换为从0开始的索引）
        index = block_id - 1
        if index < 0 or index >= len(vector_store.documents):
            return jsonify({'success': False, 'message': '文本块不存在'}), 404

        # 删除文本块
        if vector_store.delete_text_blocks([index]):
            # 保存向量存储
            save_vector_store()
            return jsonify({'success': True, 'message': '文本块删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500

    except Exception as e:
        logger.error(f"删除文本块失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/text_blocks/batch_delete', methods=['POST'])
@login_required
def batch_delete_text_blocks():
    """批量删除文本块"""
    try:
        if not vector_store:
            return jsonify({'success': False, 'message': '向量存储未初始化'}), 500

        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 将ID转换为索引（ID从1开始，索引从0开始）
        indices = [id - 1 for id in data['ids']]
        
        # 验证索引范围
        max_index = len(vector_store.documents) - 1
        invalid_indices = [idx for idx in indices if idx < 0 or idx > max_index]
        if invalid_indices:
            return jsonify({'success': False, 'message': f'无效的索引: {invalid_indices}'}), 400

        # 删除文本块
        if vector_store.delete_text_blocks(indices):
            # 保存向量存储
            save_vector_store()
            return jsonify({
                'success': True, 
                'message': f'成功删除 {len(indices)} 个文本块',
                'deleted_count': len(indices)
            })
        else:
            return jsonify({'success': False, 'message': '批量删除失败'}), 500

    except Exception as e:
        logger.error(f"批量删除文本块失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

# API路由
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if not current_user.is_admin:
        return jsonify({'error': '没有权限'}), 403
    # 获取所有用户，包括admin
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'can_upload': user.can_upload,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'is_system_admin': user.username == 'admin'  # 添加标识是否为系统管理员
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
            'can_upload': user.can_upload,
            'is_system_admin': user.username == 'admin'
        })
        
    elif request.method == 'PUT':
        data = request.get_json()
        
        try:
            # 对于admin用户，只允许修改email和密码
            if user.username == 'admin':
                if 'email' in data:
                    user.email = data['email']
                if 'password' in data and data['password']:
                    # 验证当前用户的密码（如果提供）
                    if 'current_password' in data:
                        if not user.check_password(data['current_password']):
                            return jsonify({'error': '当前密码错误'}), 400
                    user.set_password(data['password'])
                    # 同时更新系统配置中的密码
                    SystemConfig.set_value('ADMIN_PASSWORD', data['password'], 'Updated admin password')
            else:
                # 非admin用户的常规更新
                if 'email' in data:
                    user.email = data['email']
                if 'password' in data and data['password']:
                    user.set_password(data['password'])
                if 'is_admin' in data:
                    user.is_admin = data['is_admin']
                if 'can_upload' in data:
                    user.can_upload = data['can_upload']
            
            db.session.commit()
            return jsonify({'message': '用户信息已更新'})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新用户信息失败: {str(e)}")
            return jsonify({'error': f'更新用户信息失败: {str(e)}'}), 500
        
    elif request.method == 'DELETE':
        if user.username == 'admin':
            return jsonify({'error': '不能删除系统管理员账户'}), 400
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': '用户已删除'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除用户失败: {str(e)}")
            return jsonify({'error': f'删除用户失败: {str(e)}'}), 500

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

@app.route('/api/info')
@login_required
def get_info():
    """获取知识库信息"""
    try:
        info = get_knowledge_base_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"获取知识库信息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/text_blocks/<int:block_id>', methods=['PUT'])
@login_required
def update_text_block(block_id):
    """更新单个文本块内容并同步向量"""
    try:
        if not vector_store:
            return jsonify({'success': False, 'message': '向量存储未初始化'}), 500
        # 验证索引范围（block_id从1开始，需要转换为从0开始的索引）
        index = block_id - 1
        if index < 0 or index >= len(vector_store.documents):
            return jsonify({'success': False, 'message': '文本块不存在'}), 404
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'success': False, 'message': '缺少content参数'}), 400
        new_content = data['content']
        # 更新文本块内容和向量
        if vector_store.update_text_block(index, new_content):
            save_vector_store()
            return jsonify({'success': True, 'message': '文本块内容已更新'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 500
    except Exception as e:
        logger.error(f"更新文本块失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

def init_db():
    """Initialize the database and create admin user"""
    try:
        with app.app_context():
            # 确保数据库目录存在
            db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
            
            # 创建数据库表
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully")
            
            # 设置管理员凭据（如果不存在）
            if not SystemConfig.get_value('ADMIN_PASSWORD'):
                logger.info("Initializing admin credentials in database...")
                try:
                    SystemConfig.set_value('ADMIN_USERNAME', 'admin', 'Default admin username')
                    SystemConfig.set_value('ADMIN_PASSWORD', 'admin', 'Default admin password')
                    SystemConfig.set_value('ADMIN_EMAIL', 'admin@example.com', 'Default admin email')
                    logger.info("Admin credentials initialized in database")
                except Exception as e:
                    logger.error(f"Failed to set admin credentials in SystemConfig: {str(e)}")
                    raise
            
            # 初始化管理员用户
            try:
                logger.info("Initializing admin user...")
                User.init_admin()
                logger.info("Admin user initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize admin user: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to initialize database: {str(e)}")

def signal_handler(sig, frame):
    """处理终止信号"""
    print('\n正在优雅地关闭应用...')
    # 在应用上下文中清理数据库连接
    with app.app_context():
        if 'db' in globals():
            try:
                db.session.remove()
                db.engine.dispose()
            except Exception as e:
                logger.error(f"清理数据库连接时出错: {str(e)}")
    sys.exit(0)

if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    try:
        # 初始化数据库和管理员用户
        init_db()
        logger.info("Starting Flask application...")
        # 在生产环境中禁用调试模式和重载器
        app.run(
            host=config.get('server', 'host'),
            port=config.getint('server', 'port'),
            debug=config.getboolean('server', 'debug'),
            use_reloader=False  # 禁用重载器以确保信号处理正常工作
        )
    except KeyboardInterrupt:
        print('\n检测到 Ctrl+C，正在关闭应用...')
        # 在应用上下文中清理数据库连接
        with app.app_context():
            try:
                db.session.remove()
                db.engine.dispose()
            except Exception as e:
                logger.error(f"清理数据库连接时出错: {str(e)}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        logger.error(traceback.format_exc()) 