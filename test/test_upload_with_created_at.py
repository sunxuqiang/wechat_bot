#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试上传文件后创建时间是否正确设置
"""

import os
import sys
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_upload_with_created_at():
    """测试上传文件后创建时间是否正确设置"""
    try:
        from vector_store import FaissVectorStore
        from file_processors.processor_factory import ProcessorFactory
        
        logger.info("=== 测试上传文件后创建时间设置 ===")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 尝试加载现有的向量存储
        vector_store_path = "knowledge_base/vector_store"
        if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
            logger.info("加载现有向量存储...")
            vector_store.load(vector_store_path)
        
        # 创建测试文件
        test_file = "test_upload.txt"
        test_content = """这是一个测试上传文件，用于验证创建时间是否正确设置。

文件内容包含：
- 测试内容
- 创建时间验证
- 元数据检查

这个文件应该在上传后显示正确的创建时间。"""
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"创建测试文件: {test_file}")
        
        # 使用文件处理器处理文件
        processor_factory = ProcessorFactory()
        processor = processor_factory.get_processor(test_file)
        
        if not processor:
            logger.error("无法获取文件处理器")
            return False
        
        # 处理文件
        chunks = processor.process(test_file)
        logger.info(f"处理得到 {len(chunks)} 个文本块")
        
        # 检查元数据
        for i, chunk in enumerate(chunks):
            logger.info(f"文本块 {i+1}:")
            logger.info(f"  内容预览: {chunk['text'][:100]}...")
            logger.info(f"  元数据: {chunk['metadata']}")
            
            # 检查是否包含created_at
            if 'created_at' in chunk['metadata']:
                logger.info(f"  ✓ 包含创建时间: {chunk['metadata']['created_at']}")
            else:
                logger.error(f"  ✗ 缺少创建时间")
                return False
        
        # 提取文本和元数据
        text_contents = [chunk["text"] for chunk in chunks]
        metadata_list = [chunk["metadata"] for chunk in chunks]
        
        # 添加到向量存储
        success = vector_store.add(text_contents, metadata_list)
        if not success:
            logger.error("添加到向量存储失败")
            return False
        
        # 保存向量存储
        vector_store.save(vector_store_path)
        logger.info("✓ 向量存储已保存")
        
        # 验证保存的数据
        logger.info("\n=== 验证保存的数据 ===")
        for i, (text, metadata) in enumerate(vector_store.documents[-len(chunks):]):
            logger.info(f"文档 {len(vector_store.documents) - len(chunks) + i + 1}:")
            logger.info(f"  内容预览: {text[:100]}...")
            logger.info(f"  元数据: {metadata}")
            
            if 'created_at' in metadata:
                logger.info(f"  ✓ 创建时间: {metadata['created_at']}")
            else:
                logger.error(f"  ✗ 缺少创建时间")
                return False
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info(f"清理测试文件: {test_file}")
        
        logger.info("✓ 测试完成，创建时间设置正确")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_text_blocks_api():
    """测试文本块查询API"""
    try:
        from vector_store import FaissVectorStore
        
        logger.info("\n=== 测试文本块查询API ===")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 加载向量存储
        vector_store_path = "knowledge_base/vector_store"
        if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
            vector_store.load(vector_store_path)
        
        # 模拟API调用
        all_blocks = []
        for i, (content, metadata) in enumerate(vector_store.documents):
            all_blocks.append({
                'id': i + 1,
                'content': content,
                'source': metadata.get('source', '未知'),
                'create_time': metadata.get('created_at', '未知')
            })
        
        # 检查最新的文本块
        latest_blocks = all_blocks[-3:]  # 最新的3个文本块
        logger.info(f"最新的 {len(latest_blocks)} 个文本块:")
        
        for block in latest_blocks:
            logger.info(f"ID: {block['id']}")
            logger.info(f"  来源: {block['source']}")
            logger.info(f"  创建时间: {block['create_time']}")
            logger.info(f"  内容预览: {block['content'][:100]}...")
            
            if block['create_time'] == '未知':
                logger.error(f"  ✗ 创建时间为未知")
                return False
            else:
                logger.info(f"  ✓ 创建时间正确")
        
        logger.info("✓ 文本块查询API测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试文本块查询API时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始测试创建时间设置")
    
    # 测试上传文件后创建时间设置
    if test_upload_with_created_at():
        logger.info("✓ 上传文件创建时间设置测试通过")
    else:
        logger.error("✗ 上传文件创建时间设置测试失败")
        return
    
    # 测试文本块查询API
    if test_text_blocks_api():
        logger.info("✓ 文本块查询API测试通过")
    else:
        logger.error("✗ 文本块查询API测试失败")
    
    logger.info("所有测试完成")

if __name__ == "__main__":
    main() 