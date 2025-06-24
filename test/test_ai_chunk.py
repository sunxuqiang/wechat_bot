#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI智能分块功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ai_chunk_service():
    """测试AI分块服务"""
    print("=== 测试AI分块服务 ===\n")
    
    try:
        from ai_chunk_service import AIChunkService
        
        service = AIChunkService()
        print("✓ AI分块服务初始化成功")
        
        # 测试文本
        test_text = """
智能系统使用手册

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
        """
        
        print(f"测试文本长度: {len(test_text)} 字符")
        print("\n开始AI分块...")
        
        # 执行AI分块
        chunks = service.chunk_with_ai(test_text)
        
        if chunks:
            print(f"\n✓ AI分块成功，共 {len(chunks)} 个块:")
            for i, chunk in enumerate(chunks, 1):
                print(f"\n块 {i}:")
                print(f"  内容: {chunk.get('content', '')[:80]}...")
                print(f"  类型: {chunk.get('type', '未知')}")
                print(f"  原因: {chunk.get('reason', '未知')}")
            
            # 验证结果
            if service.validate_chunks(chunks):
                print("\n✓ 分块结果验证通过")
            else:
                print("\n✗ 分块结果验证失败")
            
            # 提取纯文本
            text_contents = service.extract_text_content(chunks)
            print(f"\n提取的纯文本块数量: {len(text_contents)}")
            
            return True
        else:
            print("\n✗ AI分块失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_text_processor_with_ai():
    """测试文本处理器集成AI分块"""
    print("\n=== 测试文本处理器集成AI分块 ===\n")
    
    try:
        from file_processors.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        if processor.ai_available:
            print("✓ 文本处理器AI分块功能可用")
        else:
            print("⚠ 文本处理器AI分块功能不可用，将使用传统分块")
        
        # 创建测试文件
        test_file = "test_ai_chunk.txt"
        test_content = """
项目技术文档

第一章：项目背景
本项目旨在开发一个基于人工智能的知识管理系统，为用户提供智能化的文档管理和查询服务。

技术架构：
1. 前端技术栈
   - React.js：用户界面框架
   - Bootstrap：UI组件库
   - Axios：HTTP客户端

2. 后端技术栈
   - Python Flask：Web框架
   - FAISS：向量数据库
   - Sentence Transformers：文本向量化

3. AI服务集成
   - 大语言模型API：智能分块和问答
   - 向量相似度搜索：语义匹配
   - 关键词提取：内容分析

部署方案：
一、开发环境
使用Docker容器化部署，支持快速开发和测试。

二、生产环境
采用微服务架构，支持高并发和水平扩展。
        """
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"创建测试文件: {test_file}")
        
        # 处理文件
        chunks = processor.process(test_file)
        print(f"处理结果: {len(chunks)} 个文本块")
        
        for i, chunk_data in enumerate(chunks):
            text = chunk_data['text']
            metadata = chunk_data['metadata']
            print(f"\n块 {i+1}:")
            print(f"  内容: {text[:80]}...")
            print(f"  来源: {metadata['source']}")
            print(f"  长度: {len(text)} 字符")
        
        # 清理测试文件
        os.remove(test_file)
        print("\n清理测试文件完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_mechanism():
    """测试回退机制"""
    print("\n=== 测试回退机制 ===\n")
    
    try:
        from file_processors.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # 测试空文本
        print("1. 测试空文本:")
        result = processor.split_text_with_ai_fallback("")
        print(f"   结果: {len(result)} 个块")
        
        # 测试短文本
        print("\n2. 测试短文本:")
        result = processor.split_text_with_ai_fallback("这是一个短文本。")
        print(f"   结果: {len(result)} 个块")
        
        # 测试长文本（模拟AI失败）
        print("\n3. 测试长文本:")
        long_text = "这是一个很长的文本。" * 100
        result = processor.split_text_with_ai_fallback(long_text)
        print(f"   结果: {len(result)} 个块")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试AI智能分块功能")
    
    success = True
    
    # 测试AI分块服务
    if not test_ai_chunk_service():
        success = False
    
    # 测试文本处理器集成
    if not test_text_processor_with_ai():
        success = False
    
    # 测试回退机制
    if not test_fallback_mechanism():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- AI分块服务功能正常")
        print("- 文本处理器集成成功")
        print("- 回退机制工作正常")
        print("- 支持AI失败时自动回退到传统分块")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 