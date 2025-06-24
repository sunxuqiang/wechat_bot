#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟页面上传的完整流程测试
"""

import os
import tempfile
import logging
from pathlib import Path
from file_processors.processor_factory import ProcessorFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_upload_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def create_test_file(content: str, filename: str = "test_document.txt") -> str:
    """创建测试文件"""
    temp_dir = Path("uploads/text")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = temp_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"创建测试文件: {file_path}")
    return str(file_path)

def test_web_upload_simulation():
    """测试模拟页面上传流程"""
    print("=== 模拟页面上传流程测试 ===\n")
    
    # 测试文本内容
    test_content = """项目技术文档

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
采用微服务架构，支持高并发和水平扩展。"""
    
    print(f"测试文本长度: {len(test_content)} 字符")
    
    try:
        # 1. 创建测试文件
        file_path = create_test_file(test_content)
        
        # 2. 使用ProcessorFactory（与页面上传相同的流程）
        logger.info("开始模拟页面上传流程...")
        processor_factory = ProcessorFactory()
        
        # 3. 获取处理器
        processor = processor_factory.get_processor(file_path)
        if not processor:
            logger.error("无法获取合适的处理器")
            return
        
        logger.info(f"获取到处理器: {type(processor).__name__}")
        
        # 4. 处理文件（这里会调用AI分块）
        logger.info("开始处理文件...")
        chunks = processor.process(file_path)
        
        if not chunks:
            logger.error("文件处理失败，没有生成文本块")
            return
        
        logger.info(f"处理完成，生成 {len(chunks)} 个文本块")
        
        # 5. 显示处理结果
        for i, chunk in enumerate(chunks[:5]):  # 只显示前5个块
            content = chunk.get('text', '')[:100] + '...' if len(chunk.get('text', '')) > 100 else chunk.get('text', '')
            source = chunk.get('metadata', {}).get('source', '未知')
            logger.info(f"  块 {i+1}:")
            logger.info(f"    内容: {content}")
            logger.info(f"    来源: {source}")
            logger.info(f"    长度: {len(chunk.get('text', ''))} 字符")
        
        print(f"\n✓ 页面上传流程测试成功，生成 {len(chunks)} 个文本块")
        
    except Exception as e:
        logger.error(f"页面上传流程测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n✗ 页面上传流程测试失败: {str(e)}")
    
    finally:
        # 清理测试文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("清理测试文件完成")
        except Exception as e:
            logger.error(f"清理测试文件失败: {str(e)}")

def test_ai_chunk_service_direct():
    """直接测试AI分块服务"""
    print("\n=== 直接测试AI分块服务 ===\n")
    
    try:
        from ai_chunk_service import AIChunkService
        
        # 初始化AI分块服务
        ai_service = AIChunkService()
        logger.info("AI分块服务初始化成功")
        
        # 测试文本
        test_text = """智能系统使用手册

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
   支持批量操作和实时预览。"""
        
        logger.info(f"测试文本长度: {len(test_text)} 字符")
        
        # 直接调用AI分块
        chunks = ai_service.chunk_with_ai(test_text)
        
        if chunks:
            logger.info(f"AI分块成功，生成 {len(chunks)} 个块")
            for i, chunk in enumerate(chunks[:3]):
                content = chunk.get('content', '')[:50] + '...' if len(chunk.get('content', '')) > 50 else chunk.get('content', '')
                logger.info(f"  块 {i+1}: {content}")
        else:
            logger.warning("AI分块失败，返回空结果")
            
    except Exception as e:
        logger.error(f"直接测试AI分块服务失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # 测试页面上传流程
    test_web_upload_simulation()
    
    # 直接测试AI分块服务
    test_ai_chunk_service_direct()
    
    print("\n=== 测试完成 ===")
    print("请查看 web_upload_test.log 文件获取详细日志") 