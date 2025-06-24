#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import shutil
from file_processors.processor_factory import ProcessorFactory

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_web_upload_with_fix():
    """测试页面上传时AI分块参数是否正确"""
    print("=== 测试页面上传AI分块参数修复 ===")
    
    # 测试内容
    test_content = """智能系统使用手册

第一章：系统概述
本智能系统是一款基于人工智能技术的知识管理平台，旨在帮助用户高效地管理和查询文档信息。

系统特点：
1. 智能文档处理
   支持多种文档格式，包括PDF、Word、Excel、TXT等。
   自动提取文档内容，生成结构化数据。

2. 高效搜索功能
   基于向量数据库的语义搜索。
   支持关键词匹配和相似度排序。

3. 用户友好界面
   简洁直观的操作界面。
   支持批量操作和实时预览。

第二章：安装配置
一、系统要求
操作系统：Windows 10/11, macOS 10.14+, Linux
内存：至少4GB RAM
存储：至少2GB可用空间

二、安装步骤
1. 下载安装包
   访问官方网站下载最新版本。

2. 运行安装程序
   双击安装包，按照提示完成安装。

3. 配置环境
   设置数据库连接参数。
   配置模型文件路径。

三、首次启动
启动系统后，需要：
1. 创建管理员账户
2. 初始化知识库
3. 上传测试文档"""

    def create_test_file(content):
        """创建测试文件"""
        os.makedirs('uploads/text', exist_ok=True)
        file_path = 'uploads/text/test_document.txt'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 创建测试文件: {file_path}")
        return file_path
    
    try:
        # 1. 创建测试文件
        file_path = create_test_file(test_content)
        
        # 2. 使用ProcessorFactory（与页面上传相同的流程）
        print("开始模拟页面上传流程...")
        processor_factory = ProcessorFactory()
        
        # 3. 获取处理器
        processor = processor_factory.get_processor(file_path)
        if not processor:
            print("✗ 无法获取合适的处理器")
            return
        
        print(f"✓ 获取到处理器: {type(processor).__name__}")
        
        # 4. 处理文件（这里会调用AI分块）
        print("开始处理文件...")
        chunks = processor.process(file_path)
        
        if not chunks:
            print("✗ 文件处理失败，没有生成文本块")
            return
        
        print(f"✓ 处理完成，生成 {len(chunks)} 个文本块")
        
        # 5. 显示处理结果
        for i, chunk in enumerate(chunks[:5]):  # 只显示前5个块
            content = chunk.get('text', '')[:100] + '...' if len(chunk.get('text', '')) > 100 else chunk.get('text', '')
            source = chunk.get('metadata', {}).get('source', '未知')
            print(f"  块 {i+1}:")
            print(f"    内容: {content}")
            print(f"    来源: {source}")
            print(f"    长度: {len(chunk.get('text', ''))} 字符")
        
        print(f"\n✓ 页面上传流程测试成功，生成 {len(chunks)} 个文本块")
        
        # 6. 清理测试文件
        try:
            os.remove(file_path)
            print("✓ 清理测试文件完成")
        except:
            pass
            
    except Exception as e:
        print(f"✗ 页面上传流程测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_upload_with_fix() 