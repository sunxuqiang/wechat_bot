#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动添加测试文档到知识库
"""

import os
import sys
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_test_document():
    """添加测试文档到知识库"""
    try:
        from vector_store import FaissVectorStore
        
        logger.info("=== 添加测试文档到知识库 ===")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 读取测试文档
        test_file = "test_doc.txt"
        if not os.path.exists(test_file):
            logger.error(f"测试文档不存在: {test_file}")
            return False
            
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        logger.info(f"文档内容长度: {len(content)} 字符")
        logger.info(f"文档内容预览: {content[:200]}...")
        
        # 分割文本
        from file_processors.text_processor import TextProcessor
        processor = TextProcessor()
        chunks = processor.process(test_file)
        
        logger.info(f"分割得到 {len(chunks)} 个文本块")
        
        # 提取文本和元数据
        texts = [chunk["text"] for chunk in chunks]
        metadata = [chunk["metadata"] for chunk in chunks]
        
        # 添加到向量存储
        success = vector_store.add(texts, metadata)
        
        if success:
            logger.info("✓ 测试文档添加成功")
            
            # 保存向量存储
            vector_store.save("knowledge_base/vector_store")
            logger.info("✓ 向量存储已保存")
            
            # 显示当前文档数量
            logger.info(f"当前知识库文档数量: {len(vector_store.documents)}")
            
            return True
        else:
            logger.error("✗ 测试文档添加失败")
            return False
            
    except Exception as e:
        logger.error(f"添加测试文档时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_search_after_add():
    """添加文档后测试搜索"""
    try:
        from vector_store import FaissVectorStore
        
        logger.info("=== 测试添加文档后的搜索功能 ===")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 测试搜索
        test_queries = ["测试", "文档", "知识库", "搜索"]
        
        for query in test_queries:
            logger.info(f"\n搜索查询: '{query}'")
            results = vector_store.search(query, top_k=3)
            
            if results:
                logger.info(f"✓ 找到 {len(results)} 个结果:")
                for i, (text, score, metadata) in enumerate(results, 1):
                    logger.info(f"  结果 {i}:")
                    logger.info(f"    相关度: {score:.4f}")
                    logger.info(f"    内容预览: {text[:100]}...")
                    if metadata:
                        logger.info(f"    来源: {metadata.get('source', '未知')}")
            else:
                logger.warning(f"✗ 没有找到与 '{query}' 相关的结果")
        
        return True
        
    except Exception as e:
        logger.error(f"测试搜索时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始添加测试文档")
    
    # 添加测试文档
    if add_test_document():
        logger.info("✓ 测试文档添加完成")
        
        # 测试搜索功能
        if test_search_after_add():
            logger.info("✓ 搜索功能测试完成")
        else:
            logger.error("✗ 搜索功能测试失败")
    else:
        logger.error("✗ 测试文档添加失败")
    
    logger.info("测试完成")

if __name__ == "__main__":
    main() 