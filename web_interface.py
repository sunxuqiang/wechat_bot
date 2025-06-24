from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect
import os
import shutil
from werkzeug.utils import secure_filename
from smart_kb import SmartKnowledgeBase
from pathlib import Path
import bcrypt
from datetime import datetime, timedelta
import json
import logging
from flask_wtf.csrf import CSRFProtect, generate_csrf

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session timeout
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())  # 使用随机生成的密钥
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('FLASK_CSRF_SECRET_KEY', os.urandom(24).hex())  # CSRF密钥

# 启用CSRF保护
csrf = CSRFProtect(app)

# 为所有响应添加CSRF令牌
@app.after_request
def add_csrf_token(response):
    if response.mimetype == 'text/html':
        response.set_cookie('csrf_token', generate_csrf())
    return response

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 确保知识库文档目录存在
KNOWLEDGE_BASE_DOCS = Path('knowledge_base/docs')
KNOWLEDGE_BASE_DOCS.mkdir(parents=True, exist_ok=True)

# 确保数据目录存在
DATA_DIR = Path('data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 用户数据文件路径
USER_DATA_FILE = 'user_data.json'

# 初始化知识库
try:
    kb_bot = SmartKnowledgeBase(vector_store_path=str(DATA_DIR / "vector_store"))
    kb_bot.load()  # 尝试加载已有的知识库数据
    logger.info("知识库初始化成功")
except Exception as e:
    logger.error(f"知识库初始化失败: {str(e)}")
    kb_bot = None

def load_user_data():
    """加载用户数据"""
    try:
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("成功加载用户数据")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"用户数据文件格式错误: {str(e)}")
                # 备份损坏的文件
                backup_file = f"{USER_DATA_FILE}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(USER_DATA_FILE, backup_file)
                logger.info(f"已备份损坏的用户数据文件到: {backup_file}")
            except PermissionError as e:
                logger.error(f"没有权限读取用户数据文件: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"读取用户数据文件时发生未知错误: {str(e)}")
                raise

        # 如果文件不存在或已损坏，创建默认管理员账户
        logger.info("创建默认管理员账户")
        default_data = {
            'admin': {
                'password_hash': bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()).decode(),
                'last_login': None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        try:
            # 保存默认数据
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            logger.info("成功创建默认用户数据文件")
            return default_data
        except PermissionError as e:
            logger.error(f"没有权限创建用户数据文件: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"创建用户数据文件时发生未知错误: {str(e)}")
            raise
            
    except Exception as e:
        logger.critical(f"用户数据系统初始化失败: {str(e)}")
        raise RuntimeError(f"用户认证系统初始化失败: {str(e)}")

def save_user_data(data):
    """保存用户数据"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存用户数据失败: {str(e)}")
        return False

# 初始化用户数据
user_data = load_user_data()

# 支持的文件格式
SUPPORTED_FORMATS = [
    # Microsoft Office
    '.doc', '.docx',  # Word
    '.xls', '.xlsx',  # Excel
    '.ppt', '.pptx',  # PowerPoint
    # PDF
    '.pdf',
    # 文本文件
    '.txt', '.md', '.csv', '.json'
]

@app.before_request
def check_auth():
    """检查用户认证状态"""
    # 不需要登录的路径
    public_paths = ['/login', '/static']
    
    # 检查是否是公开路径
    if any(request.path.startswith(path) for path in public_paths):
        return
    
    # 检查是否已登录
    if 'username' not in session:
        if request.is_json:
            return jsonify({'success': False, 'message': '未登录'}), 401
        return redirect('/login')

@app.route('/')
def index():
    """首页"""
    try:
        if kb_bot is None:
            logger.error("知识库未正确初始化")
            return render_template('index.html', 
                                stats={'total_documents': 0, 'total_chunks': 0, 'vector_dimension': 0},
                                documents=[],
                                supported_formats='',
                                error_message="知识库初始化失败，请检查日志")
        
        # 获取统计信息
        try:
            stats = kb_bot.get_statistics()
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            stats = {'total_documents': 0, 'total_chunks': 0, 'vector_dimension': 0}

        # 获取文档列表
        documents = []
        try:
            documents = kb_bot.document_manager.get_all_documents() if kb_bot.document_manager else []
        except Exception as e:
            logger.error(f"获取文档列表失败: {str(e)}")
        
        # 格式化支持的文件格式
        formatted_formats = [fmt.lstrip('.') for fmt in SUPPORTED_FORMATS]
        supported_formats_str = ', '.join(formatted_formats)
        
        return render_template('index.html', 
                             stats=stats,
                             documents=documents,
                             supported_formats=supported_formats_str)
    except Exception as e:
        logger.error(f"渲染首页失败: {str(e)}")
        return render_template('index.html', 
                             stats={'total_documents': 0, 'total_chunks': 0, 'vector_dimension': 0},
                             documents=[],
                             supported_formats='',
                             error_message=str(e))

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    if kb_bot is None:
        return jsonify({'error': '知识库未正确初始化'}), 500
        
    print("\n=== 开始处理文件上传 ===")
    
    if 'file' not in request.files:
        print("错误: 请求中没有文件")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        print("错误: 没有选择文件")
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        print(f"\n处理文件: {filename}")
        
        # 检查文件扩展名
        if not any(filename.lower().endswith(fmt) for fmt in SUPPORTED_FORMATS):
            return jsonify({'error': f'Unsupported file format. Supported formats are: {", ".join(SUPPORTED_FORMATS)}'}), 400
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        kb_path = KNOWLEDGE_BASE_DOCS / filename
        
        try:
            # 保存到临时目录
            print(f"保存文件到临时目录: {temp_path}")
            file.save(temp_path)
            print(f"文件大小: {os.path.getsize(temp_path) / 1024:.2f} KB")
            
            # 复制到知识库目录
            print(f"复制文件到知识库目录: {kb_path}")
            shutil.copy2(temp_path, kb_path)
            
            # 添加到知识库
            print("\n开始添加文件到知识库...")
            success = kb_bot.add_document(str(kb_path))
            
            if success:
                print("文件成功添加到知识库")
                # 保存知识库状态
                kb_bot.save()
                return jsonify({
                    'message': f'File {filename} successfully uploaded and added to knowledge base',
                    'filename': filename
                })
            else:
                print("添加到知识库失败")
                # 如果添加失败，删除复制的文件
                if kb_path.exists():
                    print(f"删除失败的文件: {kb_path}")
                    os.remove(kb_path)
                return jsonify({'error': 'Failed to add document to knowledge base'}), 500
                
        except Exception as e:
            print(f"\n处理文件时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("\n详细错误信息:")
            import traceback
            traceback.print_exc()
            
            # 发生错误时，确保清理所有文件
            if kb_path.exists():
                try:
                    print(f"删除失败的文件: {kb_path}")
                    os.remove(kb_path)
                except Exception as cleanup_error:
                    print(f"清理文件时出错: {cleanup_error}")
                    
            return jsonify({'error': str(e)}), 500
            
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_path):
                    print(f"删除临时文件: {temp_path}")
                    os.remove(temp_path)
            except Exception as cleanup_error:
                print(f"清理临时文件时出错: {cleanup_error}")

@app.route('/stats')
def get_stats():
    """获取知识库统计信息"""
    try:
        if kb_bot is None:
            return jsonify({'error': '知识库未正确初始化'}), 500
        stats = kb_bot.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/supported-formats')
def get_supported_formats():
    return jsonify({'formats': SUPPORTED_FORMATS})

@app.route('/admin')
def admin_page():
    """管理员页面"""
    return render_template('admin.html')

@app.route('/api/admin/last-login')
def get_last_login():
    """获取最后登录时间"""
    try:
        last_login = user_data.get('admin', {}).get('last_login', None)
        return jsonify({
            'success': True,
            'last_login': last_login
        })
    except Exception as e:
        logger.error(f"获取最后登录时间失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/admin/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({
                'success': False,
                'message': '新密码不能为空'
            }), 400
        
        # 生成新的密码哈希
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        
        # 更新密码
        user_data['admin']['password_hash'] = password_hash
        
        # 保存用户数据
        if save_user_data(user_data):
            logger.info("密码重置成功")
            return jsonify({
                'success': True,
                'message': '密码重置成功'
            })
        else:
            logger.error("保存密码失败")
            return jsonify({
                'success': False,
                'message': '保存密码失败'
            }), 500
            
    except Exception as e:
        logger.error(f"重置密码失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录处理"""
    if request.method == 'GET':
        # 确保session是新的
        session.clear()
        return render_template('login.html', csrf_token=generate_csrf())
    
    try:
        data = request.get_json()
        if not data:
            logger.error("登录请求没有数据")
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            logger.warning("登录请求缺少用户名或密码")
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 限制用户名长度
        if len(username) > 50 or len(password) > 100:
            logger.warning(f"用户名或密码超出长度限制: {username}")
            return jsonify({
                'success': False,
                'message': '用户名或密码长度超出限制'
            }), 400
            
        logger.info(f"尝试登录用户: {username}")
        
        try:
            if username not in user_data:
                logger.warning(f"用户名不存在: {username}")
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                }), 401
            
            # 验证密码
            stored_hash = user_data[username]['password_hash'].encode()
            if bcrypt.checkpw(password.encode(), stored_hash):
                # 更新最后登录时间
                user_data[username]['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if not save_user_data(user_data):
                    logger.error(f"更新用户登录时间失败: {username}")
                
                # 设置session
                session.clear()  # 清除旧session
                session.permanent = True  # 启用session过期时间
                session['username'] = username
                session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"用户登录成功: {username}")
                return jsonify({
                    'success': True,
                    'message': '登录成功'
                })
            else:
                logger.warning(f"密码验证失败: {username}")
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                }), 401
                
        except Exception as e:
            logger.error(f"验证密码时发生错误: {str(e)}")
            return jsonify({
                'success': False,
                'message': '验证过程发生错误，请稍后重试'
            }), 500
            
    except Exception as e:
        logger.error(f"登录过程发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器错误，请稍后重试'
        }), 500

@app.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    return redirect('/login')

# 提示词管理页面
@app.route('/prompt-management')
def prompt_management():
    """提示词管理页面"""
    return render_template('prompt_management.html')

# 获取提示词配置API
@app.route('/api/config/prompt', methods=['GET'])
def get_prompt_config():
    """获取提示词配置"""
    try:
        from config_loader import config
        prompt_file_path = config.get('api', 'ai_chunking_prompt_file', fallback='prompts/ai_chunking_prompt.txt')
        
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                ai_chunking_prompt = f.read()
        except FileNotFoundError:
            ai_chunking_prompt = ""
        
        return jsonify({
            'success': True,
            'data': {
                'ai_chunking_prompt': ai_chunking_prompt
            }
        })
    except Exception as e:
        logger.error(f"获取提示词配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500

# 保存提示词配置API
@app.route('/api/config/prompt', methods=['POST'])
def save_prompt_config():
    """保存提示词配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        ai_chunking_prompt = data.get('ai_chunking_prompt', '').strip()
        if not ai_chunking_prompt:
            return jsonify({
                'success': False,
                'message': '提示词不能为空'
            }), 400
        
        # 验证提示词是否包含必要的占位符
        if '{text}' not in ai_chunking_prompt:
            return jsonify({
                'success': False,
                'message': '提示词必须包含 {text} 占位符'
            }), 400
        
        # 获取提示词文件路径
        from config_loader import config
        prompt_file_path = config.get('api', 'ai_chunking_prompt_file', fallback='prompts/ai_chunking_prompt.txt')
        
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(prompt_file_path), exist_ok=True)
        
        # 保存到文件
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(ai_chunking_prompt)
        
        logger.info(f"提示词配置已保存到: {prompt_file_path}")
        
        return jsonify({
            'success': True,
            'message': '配置保存成功'
        })
        
    except Exception as e:
        logger.error(f"保存提示词配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存配置失败: {str(e)}'
        }), 500

# 重置提示词配置API
@app.route('/api/config/prompt/reset', methods=['POST'])
def reset_prompt_config():
    """重置提示词配置为默认值"""
    try:
        # 默认提示词
        default_prompt = """你是一个专业的文档分块专家。请将以下文本严格按照章节结构进行智能分块。

分块要求：
1. 只在遇到"文档标题"、"第X章"、"结语"这类明确的章节标题时才新建块。
2. "系统特点"、"功能模块"等内容如果没有"第X章"标题，必须归属于最近的上一章节，不要单独分块。
3. 每个章节块必须包含该章节标题及其所有内容，直到下一个"第X章"或"结语"标题为止。
4. 总块数 = 章节数 + 2（标题+结语）

5. 重要规则：
   - 第一章必须作为一个完整的块，包含"第一章：系统概述"和其后的所有内容（包括"系统特点"等）
   - 只有遇到"第二章"、"第三章"等新章节标题时才创建新块
   - 章节内的所有子内容（如"系统特点"、"功能模块"等）都必须包含在同一个块中
   - 绝对不要将章节内的内容单独分块

6. 块类型说明：
   - "文档标题"：文档的主标题
   - "章节"：主要章节内容（包含该章节的所有子内容）
   - "结语"：文档结尾部分

请严格按照以下JSON格式返回，不要添加任何其他内容：

{{
    "chunks": [
        {{
            "content": "完整的章节内容（包括章节标题和所有子内容）",
            "type": "块类型（文档标题/章节/结语）",
            "summary": "该章节的简要描述"
        }}
    ]
}}

待分块文本：
{text}"""
        
        # 获取提示词文件路径
        from config_loader import config
        prompt_file_path = config.get('api', 'ai_chunking_prompt_file', fallback='prompts/ai_chunking_prompt.txt')
        
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(prompt_file_path), exist_ok=True)
        
        # 保存默认提示词到文件
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(default_prompt)
        
        logger.info(f"提示词配置已重置为默认值: {prompt_file_path}")
        
        return jsonify({
            'success': True,
            'data': {
                'ai_chunking_prompt': default_prompt
            },
            'message': '配置已重置为默认值'
        })
        
    except Exception as e:
        logger.error(f"重置提示词配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重置配置失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 