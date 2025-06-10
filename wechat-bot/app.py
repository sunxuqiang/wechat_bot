from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import logging
from vector_store import FaissVectorStore
from typing import List, Dict, Any
from werkzeug.utils import secure_filename
import traceback
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = 'uploads'  # 上传文件保存目录

# 确保上传目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 初始化全局向量存储实例
KNOWLEDGE_BASE_DIR = Path("knowledge_base")
VECTOR_STORE_PATH = KNOWLEDGE_BASE_DIR / "vector_store"

# 确保知识库目录存在
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

try:
    logger.info("初始化向量存储...")
    vector_store = FaissVectorStore()
    
    # 检查并加载现有的向量存储
    if VECTOR_STORE_PATH.exists():
        logger.info(f"找到现有向量存储，正在从 {VECTOR_STORE_PATH} 加载...")
        try:
            vector_store.load(str(VECTOR_STORE_PATH))
            logger.info(f"已加载向量存储，包含 {len(vector_store.texts)} 条文档")
        except Exception as load_error:
            logger.error(f"加载现有向量存储失败: {load_error}")
            logger.error("创建新的向量存储实例")
            vector_store = FaissVectorStore()
    else:
        logger.info("未找到现有向量存储，创建新的实例")
except Exception as e:
    logger.error(f"初始化向量存储失败: {e}")
    logger.error(traceback.format_exc())
    vector_store = None

def save_vector_store():
    """保存向量存储到文件"""
    if not vector_store:
        logger.error("向量存储未初始化，无法保存")
        return
        
    try:
        logger.info(f"正在保存向量存储到 {VECTOR_STORE_PATH}...")
        vector_store.save(str(VECTOR_STORE_PATH))
        logger.info("向量存储保存成功")
    except Exception as e:
        logger.error(f"保存向量存储失败: {str(e)}")
        logger.error(traceback.format_exc())

@app.route('/')
def index():
    try:
        if not vector_store:
            raise Exception("向量存储未初始化")
            
        # 获取统计信息
        total_docs = str(len(vector_store.texts) if hasattr(vector_store, 'texts') else 0)
        total_chunks = str(len(vector_store.texts) if hasattr(vector_store, 'texts') else 0)
        vector_dim = str(vector_store.dimension if hasattr(vector_store, 'dimension') else 0)
        
        # 获取支持的文件格式
        formats = ', '.join(sorted(list(ALLOWED_EXTENSIONS)))
        
        return render_template('index.html', 
                             total_documents=total_docs,
                             total_chunks=total_chunks,
                             vector_dimension=vector_dim,
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
def get_stats():
    try:
        total_docs = str(len(vector_store.texts) if hasattr(vector_store, 'texts') else 0)
        total_chunks = str(len(vector_store.texts) if hasattr(vector_store, 'texts') else 0)
        vector_dim = str(vector_store.dimension if hasattr(vector_store, 'dimension') else 0)
        
        return jsonify({
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'vector_dimension': vector_dim
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    try:
        documents = []
        if hasattr(vector_store, 'documents'):
            for doc in vector_store.documents:
                preview = doc.text[:200] + '...' if len(doc.text) > 200 else doc.text
                documents.append({'preview': preview})
        return jsonify(documents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['POST'])
def add_document():
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

@app.route('/api/documents/<int:index>', methods=['DELETE'])
def delete_document(index):
    try:
        if not hasattr(vector_store, 'documents') or index >= len(vector_store.documents):
            return jsonify({'error': '文档不存在'}), 404
        
        # 从知识库中删除文档
        vector_store.documents.pop(index)
        
        # 保存向量存储
        save_vector_store()
        
        return jsonify({'message': '文档删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """搜索知识库"""
    try:
        logger.info("接收到搜索请求")
        data = request.get_json()
        if not data or 'query' not in data:
            logger.error("缺少查询参数")
            return jsonify({"error": "缺少查询参数"}), 400
            
        query = data['query'].strip()
        if not query:
            logger.error("查询内容为空")
            return jsonify({"error": "查询内容不能为空"}), 400
            
        logger.info(f"开始搜索查询: {query}")
        
        # 确保知识库已初始化
        if not vector_store:
            logger.error("知识库未初始化")
            return jsonify({"error": "知识库未初始化"}), 500
            
        # 确保知识库不为空
        if not hasattr(vector_store, 'texts') or not vector_store.texts:
            logger.warning("知识库为空")
            return jsonify({"error": "知识库为空"}), 404
            
        # 搜索知识库
        try:
            results = vector_store.search(query)
            logger.info(f"搜索完成，找到 {len(results)} 个结果")
        except Exception as search_error:
            logger.error(f"搜索失败: {search_error}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"搜索失败: {str(search_error)}"}), 500
        
        # 处理搜索结果
        processed_results = []
        for result in results:
            try:
                if isinstance(result, tuple) and len(result) >= 2:
                    content = result[0] if result[0] else ""
                    score = float(result[1]) if result[1] is not None else 0.0
                    metadata = result[2] if len(result) > 2 and result[2] else {}
                    
                    processed_results.append({
                        'content': content,
                        'score': score,
                        'metadata': metadata
                    })
            except Exception as process_error:
                logger.error(f"处理搜索结果时出错: {process_error}")
                continue
            
        if not processed_results:
            logger.warning("未找到相关内容")
            return jsonify({"results": [], "message": "未找到相关内容"})
            
        logger.info("返回搜索结果")
        return jsonify({"results": processed_results})
        
    except Exception as e:
        logger.error(f"搜索过程中发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

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

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("开始处理文件上传请求")
        
        # 检查是否有文件被上传
        if 'file' not in request.files:
            logger.error("没有文件被上传")
            return jsonify({
                'error': '没有文件被上传',
                'details': '请确保选择了要上传的文件'
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.error("文件名为空")
            return jsonify({
                'error': '没有选择文件',
                'details': '请选择要上传的文件'
            }), 400
            
        # 检查文件格式
        if not allowed_file(file.filename):
            error_msg = f'不支持的文件格式。支持的格式: {", ".join(ALLOWED_EXTENSIONS)}'
            logger.error(error_msg)
            return jsonify({
                'error': error_msg,
                'details': f'上传的文件格式为: {file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "未知"}'
            }), 400
            
        try:
            filename = secure_filename(file.filename)
            logger.info(f"处理文件: {filename}")
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logger.info(f"保存文件到: {filepath}")
            
            # 保存文件
            file.save(filepath)
            logger.info("文件保存成功")
            
            # 读取文件内容
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info("文件读取成功")
                
                # 添加到知识库
                vector_store.add([content])
                logger.info("内容已添加到知识库")
                
                # 保存向量存储
                save_vector_store()
                logger.info("向量存储已保存")
                
                # 删除临时文件
                os.remove(filepath)
                logger.info("临时文件已删除")
                
                return jsonify({
                    'message': '文件上传成功',
                    'details': {
                        'filename': filename,
                        'size': len(content),
                        'status': 'success'
                    }
                })
                
            except UnicodeDecodeError as e:
                error_msg = "文件编码错误，请确保文件是UTF-8编码的文本文件"
                logger.error(f"{error_msg}: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'error': error_msg,
                    'details': str(e)
                }), 400
                
            except Exception as e:
                error_msg = "处理文件内容时出错"
                logger.error(f"{error_msg}: {str(e)}")
                logger.error(traceback.format_exc())
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'error': error_msg,
                    'details': str(e)
                }), 500
                
        except Exception as e:
            error_msg = "保存文件时出错"
            logger.error(f"{error_msg}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': error_msg,
                'details': str(e)
            }), 500
            
    except Exception as e:
        error_msg = "处理上传请求时出错"
        logger.error(f"{error_msg}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': error_msg,
            'details': str(e)
        }), 500

@app.route('/api/load_test_doc', methods=['POST'])
def load_test_doc():
    """加载测试文档到知识库"""
    try:
        logger.info("开始加载测试文档")
        
        # 确保知识库已初始化
        if not vector_store:
            raise Exception("知识库未初始化")
            
        # 读取测试文档
        with open('test_doc.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 添加到知识库
        vector_store.add([content])
        
        # 保存知识库
        vector_store_path = Path("knowledge_base/vector_store")
        vector_store.save(str(vector_store_path))
        
        logger.info("测试文档加载成功")
        return jsonify({"message": "测试文档加载成功"})
        
    except Exception as e:
        logger.error(f"加载测试文档失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 