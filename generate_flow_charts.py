import os
import pydot
import subprocess

def generate_html(content, title):
    """生成HTML文件"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .mermaid {{
            background-color: white;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .download-btn {{
            display: block;
            width: 200px;
            margin: 20px auto;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .download-btn:hover {{
            background-color: #45a049;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="mermaid">
{content}
        </div>
        <a href="{title.lower().replace(' ', '_')}.png" class="download-btn" download>下载流程图图片</a>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>"""
    
    filename = f"{title.lower().replace(' ', '_')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    return filename

def generate_png(mermaid_content, output_file):
    """将Mermaid图表转换为PNG图片"""
    try:
        # 检查是否安装了mmdc
        subprocess.run(['mmdc', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("请先安装 mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
        return False

    # 创建临时mermaid文件
    temp_file = 'temp.mmd'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(mermaid_content)

    try:
        # 使用mmdc生成图片
        subprocess.run([
            'mmdc',
            '-i', temp_file,
            '-o', output_file,
            '-b', 'transparent',
            '-w', '2000',
            '-H', '1000'
        ], check=True)
        print(f"已生成图片: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"生成图片失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

def generate_knowledge_base_complete_flow():
    """生成知识库完整流程图"""
    graph = pydot.Dot(graph_type='digraph', rankdir='TB')
    
    # 设置节点样式
    graph.set_node_defaults(shape='box', style='rounded,filled', fillcolor='lightblue')
    
    # 用户端
    cluster0 = pydot.Subgraph(graph_name='cluster_0', label='用户端')
    cluster0.add_node(pydot.Node('A', label='用户'))
    cluster0.add_node(pydot.Node('B', label='Web界面'))
    cluster0.add_node(pydot.Node('C', label='微信客户端'))
    cluster0.add_edge(pydot.Edge('A', 'B', label='上传文档'))
    cluster0.add_edge(pydot.Edge('A', 'C', label='发送消息'))
    graph.add_subgraph(cluster0)
    
    # 后端服务
    cluster1 = pydot.Subgraph(graph_name='cluster_1', label='后端服务')
    cluster1.add_node(pydot.Node('D', label='Flask/FastAPI服务'))
    cluster1.add_edge(pydot.Edge('B', 'D', label='HTTP请求'))
    cluster1.add_edge(pydot.Edge('C', 'D', label='HTTP请求'))
    
    # 文档处理
    cluster2 = pydot.Subgraph(graph_name='cluster_2', label='文档处理')
    cluster2.add_node(pydot.Node('E', label='文档解析器'))
    cluster2.add_node(pydot.Node('E1', label='PyPDF2'))
    cluster2.add_node(pydot.Node('E2', label='python-docx'))
    cluster2.add_node(pydot.Node('E3', label='pandas'))
    cluster2.add_node(pydot.Node('E4', label='文本处理器'))
    cluster2.add_edge(pydot.Edge('D', 'E', label='文件解析'))
    cluster2.add_edge(pydot.Edge('E', 'E1', label='PDF解析'))
    cluster2.add_edge(pydot.Edge('E', 'E2', label='Word解析'))
    cluster2.add_edge(pydot.Edge('E', 'E3', label='Excel解析'))
    cluster2.add_edge(pydot.Edge('E', 'E4', label='文本解析'))
    cluster1.add_subgraph(cluster2)
    
    # 文本处理
    cluster3 = pydot.Subgraph(graph_name='cluster_3', label='文本处理')
    cluster3.add_node(pydot.Node('F', label='文本分块器'))
    cluster3.add_node(pydot.Node('G', label='向量化处理器'))
    cluster3.add_node(pydot.Node('H', label='向量存储'))
    cluster3.add_edge(pydot.Edge('E1', 'F', label='文本分块'))
    cluster3.add_edge(pydot.Edge('E2', 'F'))
    cluster3.add_edge(pydot.Edge('E3', 'F'))
    cluster3.add_edge(pydot.Edge('E4', 'F'))
    cluster3.add_edge(pydot.Edge('F', 'G', label='LangChain'))
    cluster3.add_edge(pydot.Edge('G', 'H', label='OpenAI Embeddings'))
    cluster1.add_subgraph(cluster3)
    
    # 向量存储
    cluster4 = pydot.Subgraph(graph_name='cluster_4', label='向量存储')
    cluster4.add_node(pydot.Node('I', label='向量数据库'))
    cluster4.add_node(pydot.Node('J', label='检索器'))
    cluster4.add_edge(pydot.Edge('H', 'I', label='FAISS/Chroma'))
    cluster4.add_edge(pydot.Edge('I', 'J', label='相似度搜索'))
    cluster1.add_subgraph(cluster4)
    
    # 对话处理
    cluster5 = pydot.Subgraph(graph_name='cluster_5', label='对话处理')
    cluster5.add_node(pydot.Node('K', label='上下文构建器'))
    cluster5.add_node(pydot.Node('L', label='大模型调用器'))
    cluster5.add_node(pydot.Node('M', label='响应生成器'))
    cluster5.add_edge(pydot.Edge('J', 'K', label='相关文档'))
    cluster5.add_edge(pydot.Edge('K', 'L', label='提示词工程'))
    cluster5.add_edge(pydot.Edge('L', 'M', label='GPT-4'))
    cluster1.add_subgraph(cluster5)
    
    # 缓存层
    cluster6 = pydot.Subgraph(graph_name='cluster_6', label='缓存层')
    cluster6.add_node(pydot.Node('N', label='Redis缓存'))
    cluster6.add_edge(pydot.Edge('N', 'D', label='缓存查询'))
    cluster6.add_edge(pydot.Edge('N', 'M', label='缓存响应'))
    cluster1.add_subgraph(cluster6)
    
    graph.add_subgraph(cluster1)
    
    # 响应返回
    cluster7 = pydot.Subgraph(graph_name='cluster_7', label='响应返回')
    cluster7.add_edge(pydot.Edge('M', 'B', label='HTTP响应'))
    cluster7.add_edge(pydot.Edge('M', 'C', label='HTTP响应'))
    graph.add_subgraph(cluster7)
    
    # 技术栈
    cluster8 = pydot.Subgraph(graph_name='cluster_8', label='技术栈', style='filled', fillcolor='lightpink')
    cluster8.add_node(pydot.Node('T1', label='前端: Vue.js + Element UI'))
    cluster8.add_node(pydot.Node('T2', label='后端: Flask/FastAPI'))
    cluster8.add_node(pydot.Node('T3', label='向量化: OpenAI Embeddings'))
    cluster8.add_node(pydot.Node('T4', label='存储: FAISS/Chroma + Redis'))
    cluster8.add_node(pydot.Node('T5', label='大模型: GPT-4'))
    graph.add_subgraph(cluster8)
    
    # 性能优化
    cluster9 = pydot.Subgraph(graph_name='cluster_9', label='性能优化', style='filled', fillcolor='lightblue')
    cluster9.add_node(pydot.Node('P1', label='并发处理'))
    cluster9.add_node(pydot.Node('P2', label='批量向量化'))
    cluster9.add_node(pydot.Node('P3', label='缓存机制'))
    cluster9.add_node(pydot.Node('P4', label='异步处理'))
    graph.add_subgraph(cluster9)
    
    # 安全措施
    cluster10 = pydot.Subgraph(graph_name='cluster_10', label='安全措施', style='filled', fillcolor='lightgreen')
    cluster10.add_node(pydot.Node('S1', label='API认证'))
    cluster10.add_node(pydot.Node('S2', label='请求限流'))
    cluster10.add_node(pydot.Node('S3', label='敏感信息过滤'))
    cluster10.add_node(pydot.Node('S4', label='超时控制'))
    graph.add_subgraph(cluster10)
    
    # 保存图片
    output_path = os.path.join('docs', 'knowledge_base_complete_flow.png')
    graph.write_png(output_path)
    return output_path

def generate_knowledge_upload_flow():
    """生成知识库上传流程图"""
    graph = pydot.Dot(graph_type='digraph', rankdir='TB')
    
    # 设置节点样式
    graph.set_node_defaults(shape='box', style='rounded,filled', fillcolor='lightblue')
    
    # 添加节点
    graph.add_node(pydot.Node('A', label='开始'))
    graph.add_node(pydot.Node('B', label='用户上传文档'))
    graph.add_node(pydot.Node('C', label='文档类型判断', shape='diamond'))
    graph.add_node(pydot.Node('D', label='PDF解析器'))
    graph.add_node(pydot.Node('E', label='Word解析器'))
    graph.add_node(pydot.Node('F', label='Excel解析器'))
    graph.add_node(pydot.Node('G', label='文本解析器'))
    graph.add_node(pydot.Node('H', label='文本预处理'))
    graph.add_node(pydot.Node('I', label='文本分块'))
    graph.add_node(pydot.Node('J', label='向量化处理'))
    graph.add_node(pydot.Node('K', label='存储到向量数据库'))
    graph.add_node(pydot.Node('L', label='更新元数据'))
    graph.add_node(pydot.Node('M', label='结束'))
    
    # 添加边
    graph.add_edge(pydot.Edge('A', 'B'))
    graph.add_edge(pydot.Edge('B', 'C'))
    graph.add_edge(pydot.Edge('C', 'D', label='PDF'))
    graph.add_edge(pydot.Edge('C', 'E', label='Word'))
    graph.add_edge(pydot.Edge('C', 'F', label='Excel'))
    graph.add_edge(pydot.Edge('C', 'G', label='Text'))
    graph.add_edge(pydot.Edge('D', 'H'))
    graph.add_edge(pydot.Edge('E', 'H'))
    graph.add_edge(pydot.Edge('F', 'H'))
    graph.add_edge(pydot.Edge('G', 'H'))
    graph.add_edge(pydot.Edge('H', 'I'))
    graph.add_edge(pydot.Edge('I', 'J'))
    graph.add_edge(pydot.Edge('J', 'K'))
    graph.add_edge(pydot.Edge('K', 'L'))
    graph.add_edge(pydot.Edge('L', 'M'))
    
    # 保存图片
    output_path = os.path.join('docs', 'knowledge_upload_flow.png')
    graph.write_png(output_path)
    return output_path

def generate_wechat_query_flow():
    """生成微信查询流程图"""
    graph = pydot.Dot(graph_type='digraph', rankdir='TB')
    
    # 设置节点样式
    graph.set_node_defaults(shape='box', style='rounded,filled', fillcolor='lightblue')
    
    # 添加节点
    graph.add_node(pydot.Node('A', label='开始'))
    graph.add_node(pydot.Node('B', label='接收用户消息'))
    graph.add_node(pydot.Node('C', label='消息预处理'))
    graph.add_node(pydot.Node('D', label='向量化查询'))
    graph.add_node(pydot.Node('E', label='相似度搜索'))
    graph.add_node(pydot.Node('F', label='获取相关文档'))
    graph.add_node(pydot.Node('G', label='构建提示词'))
    graph.add_node(pydot.Node('H', label='调用大模型'))
    graph.add_node(pydot.Node('I', label='生成回复'))
    graph.add_node(pydot.Node('J', label='返回给用户'))
    graph.add_node(pydot.Node('K', label='结束'))
    
    # 添加边
    graph.add_edge(pydot.Edge('A', 'B'))
    graph.add_edge(pydot.Edge('B', 'C'))
    graph.add_edge(pydot.Edge('C', 'D'))
    graph.add_edge(pydot.Edge('D', 'E'))
    graph.add_edge(pydot.Edge('E', 'F'))
    graph.add_edge(pydot.Edge('F', 'G'))
    graph.add_edge(pydot.Edge('G', 'H'))
    graph.add_edge(pydot.Edge('H', 'I'))
    graph.add_edge(pydot.Edge('I', 'J'))
    graph.add_edge(pydot.Edge('J', 'K'))
    
    # 保存图片
    output_path = os.path.join('docs', 'wechat_query_flow.png')
    graph.write_png(output_path)
    return output_path

def convert_html_to_png(html_file, output_png):
    """将 HTML 文件转换为 PNG 图片"""
    try:
        # 使用 wkhtmltopdf 的完整路径
        wkhtmltoimage_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe"
        if not os.path.exists(wkhtmltoimage_path):
            print(f"未找到 wkhtmltoimage 工具，请安装 wkhtmltopdf 并确保路径正确: {wkhtmltoimage_path}")
            return
        subprocess.run([wkhtmltoimage_path, html_file, output_png], check=True)
        print(f"已成功将 {html_file} 转换为 {output_png}")
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    print("开始生成流程图...")
    
    # 生成知识库完整流程图
    png_file = generate_knowledge_base_complete_flow()
    print(f"已生成知识库完整流程图图片: {png_file}")
    
    # 生成知识库上传流程图
    png_file = generate_knowledge_upload_flow()
    print(f"已生成知识库上传流程图图片: {png_file}")
    
    # 生成微信查询流程图
    png_file = generate_wechat_query_flow()
    print(f"已生成微信查询流程图图片: {png_file}")
    
    # 将 knowledge_base_complete_flow.html 转换为 PNG
    html_file = os.path.join('docs', 'knowledge_base_complete_flow.html')
    output_png = os.path.join('docs', 'knowledge_base_complete_flow_from_html.png')
    convert_html_to_png(html_file, output_png)
    
    print("\n所有流程图生成完成！")
    print("PNG图片文件可以直接使用") 