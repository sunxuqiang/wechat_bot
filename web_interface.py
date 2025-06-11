from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import shutil
from werkzeug.utils import secure_filename
from knowledge_bot import KnowledgeBot
from pathlib import Path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 确保知识库文档目录存在
KNOWLEDGE_BASE_DOCS = Path('knowledge_base/docs')
KNOWLEDGE_BASE_DOCS.mkdir(parents=True, exist_ok=True)

# 初始化知识库
kb_bot = KnowledgeBot()

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

@app.route('/')
def index():
    try:
        # 获取统计信息
        stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'vector_dimension': 0
        }
        try:
            stats = kb_bot.get_statistics()
        except Exception as e:
            print(f"Error getting statistics: {str(e)}")

        # 获取文档列表
        documents = []
        try:
            # 这里可以添加获取文档列表的逻辑
            if hasattr(kb_bot, 'get_documents'):
                documents = kb_bot.get_documents()
        except Exception as e:
            print(f"Error getting documents: {str(e)}")
        
        # 格式化支持的文件格式
        formatted_formats = [fmt.lstrip('.') for fmt in SUPPORTED_FORMATS]
        supported_formats_str = ', '.join(formatted_formats)
        
        return render_template('index.html', 
                             stats=stats,
                             documents=documents,
                             supported_formats=supported_formats_str)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        # 返回带有默认值的模板
        formatted_formats = [fmt.lstrip('.') for fmt in SUPPORTED_FORMATS]
        supported_formats_str = ', '.join(formatted_formats)
        return render_template('index.html', 
                             stats={'total_documents': 0, 'total_chunks': 0, 'vector_dimension': 0},
                             documents=[],
                             supported_formats=supported_formats_str)

@app.route('/upload', methods=['POST'])
def upload_file():
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
    try:
        stats = kb_bot.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/supported-formats')
def get_supported_formats():
    return jsonify({'formats': SUPPORTED_FORMATS})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 