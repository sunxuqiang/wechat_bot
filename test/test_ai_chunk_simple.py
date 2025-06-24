#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from ai_chunk_service import AIChunkService

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_ai_chunking():
    """测试AI分块功能"""
    print("=== 测试AI分块功能 ===")
    
    # 测试文本
    test_text = """第一章：项目背景
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
使用Docker容器化部署，支持快速开发和测试。"""
    
    print(f"测试文本长度: {len(test_text)} 字符")
    
    try:
        # 初始化AI分块服务
        ai_service = AIChunkService()
        print("✓ AI分块服务初始化成功")
        
        # 执行AI分块
        print("开始AI分块...")
        chunks = ai_service.chunk_with_ai(test_text)
        
        if chunks:
            print(f"✓ AI分块成功，生成 {len(chunks)} 个文本块")
            for i, chunk in enumerate(chunks, 1):
                print(f"\n块 {i}:")
                print(f"  内容: {chunk.get('content', 'N/A')}")
                print(f"  类型: {chunk.get('type', 'N/A')}")
                print(f"  原因: {chunk.get('reason', 'N/A')}")
                print(f"  长度: {len(chunk.get('content', ''))} 字符")
        else:
            print("✗ AI分块失败")
            
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_chunking() 