import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from knowledge_bot import KnowledgeBot

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 初始化知识库
try:
    print("正在初始化知识库...")
    knowledge_bot = KnowledgeBot()
    print("知识库初始化成功")
except Exception as e:
    print(f"初始化知识库失败: {e}")
    knowledge_bot = None

# 确保templates目录存在
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)
print(f"模板目录已确认: {templates_dir}")

# 确保知识库目录结构存在
kb_dir = Path("knowledge_base")
kb_dir.mkdir(exist_ok=True)
docs_dir = kb_dir / "docs"
docs_dir.mkdir(exist_ok=True)
index_dir = kb_dir / "faiss_index"
index_dir.mkdir(exist_ok=True)
print(f"知识库目录结构已确认: {kb_dir}")

def get_knowledge_base_info():
    """获取知识库信息"""
    print("获取知识库信息...")
    if knowledge_bot is None:
        return {"error": "Knowledge bot initialization failed"}
        
    try:
        # 获取知识库统计信息
        stats = knowledge_bot.get_statistics()
        
        info = {
            "index_exists": False,
            "docs_count": stats.get("total_documents", 0),
            "docs": [],
            "stats": stats,
            "total_size": stats.get("index_size_bytes", 0),
            "supported_formats": stats.get("supported_formats", []),
            "index_info": None
        }
        
        # 检查索引文件
        index_dir = Path("knowledge_base/faiss_index")
        info["index_exists"] = index_dir.exists()
        if index_dir.exists():
            try:
                # 获取索引文件信息
                index_files = list(index_dir.rglob("*"))
                index_size = sum(f.stat().st_size for f in index_files if f.is_file())
                info["index_info"] = {
                    "size": index_size,
                    "size_formatted": format_size(index_size),
                    "files_count": len([f for f in index_files if f.is_file()]),
                    "last_modified": datetime.fromtimestamp(max(f.stat().st_mtime for f in index_files if f.is_file())).strftime("%Y-%m-%d %H:%M:%S")
                }
            except Exception as e:
                print(f"获取索引信息时出错: {e}")
        
        # 获取文档列表
        if stats.get("documents"):
            for doc in stats["documents"]:
                try:
                    file_path = Path(doc["path"])
                    if file_path.exists():
                        size = file_path.stat().st_size
                        info["docs"].append({
                            "id": len(info["docs"]),
                            "path": doc["path"],
                            "size": size,
                            "size_formatted": format_size(size),
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                            "chunk_count": doc.get("chunk_count", 0)
                        })
                except Exception as e:
                    print(f"获取文档信息时出错: {e}")
        
        return info
    except Exception as e:
        print(f"获取知识库信息时出错: {e}")
        return {"error": str(e)}

def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/info')
def get_info():
    """获取知识库信息"""
    info = get_knowledge_base_info()
    return jsonify(info if info else {"error": "Knowledge base not found"})

@app.route('/api/delete', methods=['POST'])
def delete_content():
    """删除选中的内容"""
    try:
        if knowledge_bot is None:
            return jsonify({"error": "Knowledge bot not initialized"}), 500
            
        data = request.json
        selections = data.get('selections', [])
        doc_ids = data.get('doc_ids', [])
        
        kb_dir = Path("knowledge_base")
        if not kb_dir.exists():
            return jsonify({"error": "Knowledge base not found"}), 404
            
        deleted_items = []
        
        # 删除索引
        if 'index' in selections:
            index_file = kb_dir / "faiss_index"
            if index_file.exists():
                shutil.rmtree(index_file)
                # 重新初始化向量存储
                knowledge_bot._init_vector_store()
                deleted_items.append("索引文件")
        
        # 获取当前文档列表
        info = get_knowledge_base_info()
        current_docs = info.get('docs', [])
        
        # 删除所有文档
        if 'all_docs' in selections:
            docs_dir = kb_dir / "docs"
            if docs_dir.exists():
                # 先从知识库中删除所有文档
                for doc in current_docs:
                    knowledge_bot.remove_document(doc['path'])
                # 然后删除文件
                shutil.rmtree(docs_dir)
                docs_dir.mkdir(exist_ok=True)
                deleted_items.append("所有文档")
        
        # 删除特定文档
        elif doc_ids:
            docs_dir = kb_dir / "docs"
            if docs_dir.exists():
                for doc_id in doc_ids:
                    try:
                        doc_id = int(doc_id)
                        if 0 <= doc_id < len(current_docs):
                            doc = current_docs[doc_id]
                            # 先从知识库中删除文档
                            if knowledge_bot.remove_document(doc['path']):
                                # 然后删除文件
                                doc_path = Path(doc['path'])
                                if doc_path.exists():
                                    os.remove(doc_path)
                                deleted_items.append(f"文档: {doc['path']}")
                    except (ValueError, IndexError) as e:
                        print(f"删除文档时出错: {e}")
                        continue
        
        # 删除统计信息
        if 'stats' in selections:
            stats_file = kb_dir / "stats.json"
            if stats_file.exists():
                os.remove(stats_file)
                deleted_items.append("统计信息")
        
        # 获取更新后的信息
        updated_info = get_knowledge_base_info()
        
        return jsonify({
            "success": True,
            "deleted_items": deleted_items,
            "info": updated_info
        })
        
    except Exception as e:
        print(f"删除内容时出错: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """上传文件到知识库"""
    try:
        print("开始处理文件上传请求...")
        
        if knowledge_bot is None:
            print("错误：知识库未初始化")
            return jsonify({"error": "Knowledge bot not initialized"}), 500
            
        if 'files[]' not in request.files:
            print("错误：未提供文件")
            return jsonify({"error": "No files provided"}), 400
            
        files = request.files.getlist('files[]')
        if not files:
            print("错误：未选择文件")
            return jsonify({"error": "No files selected"}), 400
            
        print(f"收到 {len(files)} 个文件")
        results = []
        
        for file in files:
            if file.filename:
                try:
                    print(f"处理文件: {file.filename}")
                    # 检查文件类型
                    file_ext = Path(file.filename).suffix.lower()
                    if file_ext not in knowledge_bot.loader_mapping:
                        print(f"不支持的文件类型: {file_ext}")
                        results.append({
                            "filename": file.filename,
                            "success": False,
                            "error": f"不支持的文件类型: {file_ext}"
                        })
                        continue
                    
                    # 确保文档目录存在
                    docs_dir = Path("knowledge_base/docs")
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 保存文件
                    file_path = docs_dir / file.filename
                    print(f"保存文件到: {file_path}")
                    
                    # 如果文件已存在，先尝试从知识库中删除
                    if file_path.exists():
                        try:
                            print(f"删除已存在的文件: {file_path}")
                            knowledge_bot.remove_document(str(file_path))
                        except Exception as e:
                            print(f"删除已存在的文档时出错: {e}")
                    
                    # 保存新文件
                    file.save(str(file_path))
                    print(f"文件已保存: {file_path}")
                    
                    # 添加到知识库
                    print(f"添加文件到知识库: {file_path}")
                    success = knowledge_bot.add_document(str(file_path))
                    
                    if success:
                        print(f"文件添加成功: {file.filename}")
                        results.append({
                            "filename": file.filename,
                            "success": True,
                            "error": None
                        })
                    else:
                        print(f"添加到知识库失败: {file.filename}")
                        # 如果添加失败，删除已保存的文件
                        try:
                            file_path.unlink()
                            print(f"已删除失败的文件: {file_path}")
                        except Exception as e:
                            print(f"删除失败的文件时出错: {e}")
                        results.append({
                            "filename": file.filename,
                            "success": False,
                            "error": "添加到知识库失败"
                        })
                except Exception as e:
                    print(f"处理文件 {file.filename} 时出错: {e}")
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": str(e)
                    })
        
        # 获取更新后的知识库信息
        print("获取更新后的知识库信息")
        info = get_knowledge_base_info()
        
        print("上传处理完成")
        return jsonify({
            "results": results,
            "info": info
        })
        
    except Exception as e:
        print(f"上传处理过程中发生错误: {e}")
        return jsonify({"error": str(e)}), 500

# 创建HTML模板
template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>知识库管理工具</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333;
            margin-bottom: 20px;
        }
        .info-section {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        .upload-section {
            margin: 20px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border: 2px dashed #ccc;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .upload-section:hover {
            background-color: #e9ecef;
            border-color: #adb5bd;
        }
        .upload-section.dragover {
            background-color: #e9ecef;
            border-color: #007bff;
        }
        .upload-section input[type="file"] {
            display: none;
        }
        .upload-label {
            display: block;
            text-align: center;
            padding: 20px;
            cursor: pointer;
        }
        .upload-progress {
            margin: 10px 0;
            padding: 10px;
            background-color: #fff;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .progress-bar {
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }
        .progress-bar .fill {
            height: 100%;
            background-color: #007bff;
            border-radius: 10px;
            transition: width 0.3s ease;
            color: white;
            text-align: center;
            line-height: 20px;
            font-size: 12px;
            position: absolute;
            left: 0;
            top: 0;
        }
        .file-list {
            margin-top: 10px;
            max-height: 300px;
            overflow-y: auto;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background-color: white;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .file-info .filename {
            font-weight: 500;
        }
        .file-info .filesize {
            color: #6c757d;
            font-size: 0.9em;
        }
        .file-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            border-radius: 4px;
            display: none;
        }
        .alert-success {
            color: #155724;
            background-color: #d4edda;
            border-color: #c3e6cb;
        }
        .alert-danger {
            color: #721c24;
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            background-color: rgba(0,0,0,0.1);
            border-radius: 4px;
        }
        button {
            padding: 8px 16px;
            margin-right: 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background-color: #007bff;
            color: white;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: #0056b3;
        }
        button.delete {
            background-color: #dc3545;
        }
        button.delete:hover {
            background-color: #c82333;
        }
        .checkbox-group {
            margin: 10px 0;
        }
        .checkbox-group label {
            margin-right: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>知识库管理工具</h1>
        
        <div id="alert" class="alert"></div>
        
        <div class="info-section">
            <h2>知识库状态</h2>
            <div id="kb-info"></div>
        </div>
        
        <div class="upload-section" id="upload-area">
            <input type="file" id="file-input" multiple>
            <label for="file-input" class="upload-label">
                <div>
                    <h3>上传文件</h3>
                    <p>点击或拖拽文件到此处上传</p>
                    <p id="supported-formats"></p>
                </div>
            </label>
            <div id="file-list" class="file-list"></div>
        </div>
        
        <div class="actions">
            <h2>操作选项</h2>
            <div class="checkbox-group">
                <input type="checkbox" id="select-index"> <label for="select-index">索引文件</label>
                <input type="checkbox" id="select-all-docs"> <label for="select-all-docs">所有文档</label>
                <input type="checkbox" id="select-stats"> <label for="select-stats">统计信息</label>
            </div>
            <div class="docs-section">
                <h3>文档列表</h3>
                <div id="docs-table"></div>
            </div>
            <button onclick="deleteSelected()" class="delete">删除选中内容</button>
            <button onclick="refreshInfo()">刷新状态</button>
        </div>
        
        <div id="loading" class="loading">处理中...</div>
    </div>

    <script>
    // 页面加载时初始化
    document.addEventListener('DOMContentLoaded', () => {
        console.log('Page loaded, initializing...');
        initializeUploadArea();
        initializeButtons();
        refreshInfo();
    });

    // 初始化上传区域
    function initializeUploadArea() {
        console.log('Initializing upload area...');
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        
        if (!uploadArea || !fileInput) {
            console.error('Upload elements not found');
            return;
        }
        
        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            console.log('Files dropped:', files.length);
            handleFiles(files);
        });
        
        // 点击上传
        fileInput.addEventListener('change', (e) => {
            console.log('Files selected:', e.target.files.length);
            handleFiles(e.target.files);
        });
    }

    // 初始化按钮事件
    function initializeButtons() {
        const deleteButton = document.querySelector('button.delete');
        if (deleteButton) {
            deleteButton.onclick = deleteSelected;
        }
        
        const refreshButton = document.querySelector('button:not(.delete)');
        if (refreshButton) {
            refreshButton.onclick = refreshInfo;
        }
    }

    // 处理文件上传
    function handleFiles(files) {
        if (!files || files.length === 0) {
            console.log('No files selected');
            return;
        }
        
        console.log('Processing files:', files.length);
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        
        const formData = new FormData();
        Array.from(files).forEach(file => {
            console.log('Adding file:', file.name);
            formData.append('files[]', file);
            addFileToList(file);
        });
        
        // 显示上传进度区域
        const progressContainer = document.createElement('div');
        progressContainer.className = 'upload-progress';
        progressContainer.innerHTML = `
            <div class="progress-bar">
                <div class="fill" style="width: 0%">0%</div>
            </div>
        `;
        fileList.insertBefore(progressContainer, fileList.firstChild);
        
        // 发送上传请求
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);
        
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                const fill = progressContainer.querySelector('.fill');
                if (fill) {
                    fill.style.width = percentComplete + '%';
                    fill.textContent = Math.round(percentComplete) + '%';
                }
                console.log('Upload progress:', percentComplete + '%');
            }
        };
        
        xhr.onload = function() {
            console.log('Upload completed, status:', xhr.status);
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.error) {
                        showAlert(response.error, 'danger');
                        return;
                    }
                    
                    // 更新文件状态
                    response.results.forEach(result => {
                        updateFileStatus(result.filename, result.success, result.error);
                    });
                    
                    // 更新知识库信息
                    updateKnowledgeBaseInfo(response.info);
                    
                    // 显示成功消息
                    const successCount = response.results.filter(r => r.success).length;
                    if (successCount > 0) {
                        showAlert(`成功上传 ${successCount} 个文件`, 'success');
                    }
                    
                    // 3秒后移除进度条
                    setTimeout(() => {
                        progressContainer.remove();
                    }, 3000);
                    
                } catch (e) {
                    console.error('Error parsing response:', e);
                    showAlert('解析响应失败: ' + e, 'danger');
                }
            } else {
                console.error('Upload failed:', xhr.statusText);
                showAlert('上传失败: ' + xhr.statusText, 'danger');
            }
            
            // 清空文件输入
            document.getElementById('file-input').value = '';
        };
        
        xhr.onerror = function() {
            console.error('Network error during upload');
            showAlert('上传失败: 网络错误', 'danger');
            progressContainer.remove();
        };
        
        // 开始上传
        console.log('Starting upload...');
        xhr.send(formData);
    }

    // 添加文件到列表
    function addFileToList(file) {
        console.log('Adding file to list:', file.name);
        const fileList = document.getElementById('file-list');
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div class="file-info">
                <span class="filename">${file.name}</span>
                <span class="filesize">(${formatFileSize(file.size)})</span>
            </div>
            <div class="file-status">
                <span class="status" data-filename="${file.name}">准备上传...</span>
            </div>
        `;
        fileList.appendChild(item);
    }

    // 更新文件状态
    function updateFileStatus(filename, success, error) {
        console.log('Updating file status:', filename, success, error);
        const statusElement = document.querySelector(`[data-filename="${filename}"]`);
        if (statusElement) {
            statusElement.className = `status ${success ? 'success' : 'error'}`;
            statusElement.textContent = success ? '上传成功' : `上传失败: ${error}`;
        }
    }

    // 格式化文件大小
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 刷新知识库信息
    function refreshInfo() {
        console.log('Refreshing knowledge base info...');
        document.getElementById('loading').style.display = 'block';
        
        fetch('/api/info')
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                if (data.error) {
                    showAlert(data.error, 'danger');
                    return;
                }
                updateKnowledgeBaseInfo(data);
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                console.error('Error refreshing info:', error);
                showAlert('获取信息失败: ' + error, 'danger');
            });
    }

    // 更新知识库信息
    function updateKnowledgeBaseInfo(info) {
        console.log('Updating knowledge base info:', info);
        
        // 更新支持的格式信息
        if (info.supported_formats) {
            const formats = info.supported_formats.join(', ');
            document.getElementById('supported-formats').textContent = `支持的格式: ${formats}`;
        }
        
        // 更新知识库状态
        let infoHtml = '<div style="padding: 10px; background-color: white; border-radius: 4px;">';
        
        // 显示索引信息
        infoHtml += '<div style="margin-bottom: 15px;">';
        infoHtml += `<h3 style="margin: 0 0 10px 0;">索引状态</h3>`;
        if (info.index_exists) {
            infoHtml += `<p style="margin: 5px 0;">状态: <span style="color: #28a745;">存在</span></p>`;
            if (info.index_info) {
                infoHtml += `<p style="margin: 5px 0;">文件数量: ${info.index_info.files_count}个</p>`;
                infoHtml += `<p style="margin: 5px 0;">索引大小: ${info.index_info.size_formatted}</p>`;
                infoHtml += `<p style="margin: 5px 0;">最后修改: ${info.index_info.last_modified}</p>`;
            }
        } else {
            infoHtml += `<p style="margin: 5px 0;">状态: <span style="color: #dc3545;">不存在</span></p>`;
        }
        infoHtml += '</div>';
        
        // 显示文档信息
        infoHtml += '<div style="margin-bottom: 15px;">';
        infoHtml += `<h3 style="margin: 0 0 10px 0;">文档状态</h3>`;
        infoHtml += `<p style="margin: 5px 0;">文档总数: ${info.docs_count}个</p>`;
        if (info.total_size) {
            infoHtml += `<p style="margin: 5px 0;">总大小: ${formatFileSize(info.total_size)}</p>`;
        }
        infoHtml += '</div>';
        
        // 显示统计信息
        if (info.stats) {
            infoHtml += '<div>';
            infoHtml += `<h3 style="margin: 0 0 10px 0;">详细统计</h3>`;
            infoHtml += `<pre style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">${JSON.stringify(info.stats, null, 2)}</pre>`;
            infoHtml += '</div>';
        }
        
        infoHtml += '</div>';
        document.getElementById('kb-info').innerHTML = infoHtml;
        
        // 更新文档表格
        updateDocumentsTable(info.docs);
    }

    // 更新文档表格
    function updateDocumentsTable(docs) {
        console.log('Updating documents table:', docs);
        const tableContainer = document.getElementById('docs-table');
        
        if (docs && docs.length > 0) {
            let tableHtml = `
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <th style="padding: 8px; text-align: left;">
                            <input type="checkbox" onchange="toggleAllDocs(this)">
                        </th>
                        <th style="padding: 8px; text-align: left;">文件名</th>
                        <th style="padding: 8px; text-align: left;">大小</th>
                        <th style="padding: 8px; text-align: left;">块数</th>
                        <th style="padding: 8px; text-align: left;">修改时间</th>
                    </tr>
            `;
            
            docs.forEach(doc => {
                tableHtml += `
                    <tr>
                        <td style="padding: 8px; border-top: 1px solid #dee2e6;">
                            <input type="checkbox" class="doc-checkbox" data-id="${doc.id}">
                        </td>
                        <td style="padding: 8px; border-top: 1px solid #dee2e6;">${doc.path}</td>
                        <td style="padding: 8px; border-top: 1px solid #dee2e6;">${doc.size_formatted}</td>
                        <td style="padding: 8px; border-top: 1px solid #dee2e6;">${doc.chunk_count || 0}</td>
                        <td style="padding: 8px; border-top: 1px solid #dee2e6;">${doc.modified}</td>
                    </tr>
                `;
            });
            
            tableHtml += '</table>';
            tableContainer.innerHTML = tableHtml;
        } else {
            tableContainer.innerHTML = '<p>没有文档</p>';
        }
    }

    // 切换所有文档的选中状态
    function toggleAllDocs(checkbox) {
        document.querySelectorAll('.doc-checkbox').forEach(doc => {
            doc.checked = checkbox.checked;
        });
    }

    // 删除选中内容
    function deleteSelected() {
        console.log('Deleting selected items...');
        const selections = [];
        if (document.getElementById('select-index').checked) selections.push('index');
        if (document.getElementById('select-all-docs').checked) selections.push('all_docs');
        if (document.getElementById('select-stats').checked) selections.push('stats');
        
        const docIds = [];
        if (!document.getElementById('select-all-docs').checked) {
            document.querySelectorAll('.doc-checkbox:checked').forEach(checkbox => {
                docIds.push(checkbox.dataset.id);
            });
        }
        
        if (selections.length === 0 && docIds.length === 0) {
            showAlert('请选择要删除的内容', 'danger');
            return;
        }
        
        if (!confirm('确定要删除选中的内容吗？此操作不可恢复！')) {
            return;
        }
        
        document.getElementById('loading').style.display = 'block';
        
        fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ selections, doc_ids: docIds })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            if (data.error) {
                showAlert(data.error, 'danger');
                return;
            }
            
            // 清空选中状态
            document.getElementById('select-index').checked = false;
            document.getElementById('select-all-docs').checked = false;
            document.getElementById('select-stats').checked = false;
            
            // 显示删除结果
            if (data.deleted_items && data.deleted_items.length > 0) {
                showAlert('已删除以下内容：\n' + data.deleted_items.join('\n'), 'success');
            } else {
                showAlert('未删除任何内容', 'danger');
            }
            
            // 更新知识库信息
            updateKnowledgeBaseInfo(data.info);
        })
        .catch(error => {
            document.getElementById('loading').style.display = 'none';
            console.error('Error deleting items:', error);
            showAlert('删除失败: ' + error, 'danger');
        });
    }

    // 显示提示信息
    function showAlert(message, type) {
        console.log('Showing alert:', type, message);
        const alert = document.getElementById('alert');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alert.style.display = 'block';
        
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    }
    </script>
</body>
</html>
"""

# 创建模板文件
with open(templates_dir / "index.html", "w", encoding="utf-8") as f:
    f.write(template_content)

if __name__ == '__main__':
    print("=== 知识库管理工具 Web 界面 ===")
    print("正在启动服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True) 