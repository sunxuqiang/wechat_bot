#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索修复效果
"""

import os
import sys
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_functionality():
    """测试搜索功能"""
    try:
        # 导入向量存储
        from vector_store import FaissVectorStore
        
        logger.info("=== 开始测试搜索功能 ===")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 尝试加载现有的向量存储
        vector_store_path = "knowledge_base/vector_store"
        if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
            logger.info("加载现有向量存储...")
            vector_store.load(vector_store_path)
        
        # 检查是否有现有数据
        if not vector_store.documents:
            logger.warning("向量存储中没有文档，请先上传一些文档")
            return False
            
        logger.info(f"当前知识库文档数量: {len(vector_store.documents)}")
        
        # 显示一些文档示例
        logger.info("\n文档示例:")
        for i, (text, metadata) in enumerate(vector_store.documents[:3]):
            logger.info(f"文档 {i+1}:")
            logger.info(f"  内容预览: {text[:100]}...")
            logger.info(f"  元数据: {metadata}")
            logger.info()
        
        # 测试搜索
        test_queries = [
            "测试",
            "文档",
            "内容",
            "知识库",
            "搜索"
        ]
        
        logger.info("=== 开始搜索测试 ===")
        for query in test_queries:
            logger.info(f"\n搜索查询: '{query}'")
            results = vector_store.search(query, top_k=3)
            
            if results:
                logger.info(f"找到 {len(results)} 个结果:")
                for i, (text, score, metadata) in enumerate(results, 1):
                    logger.info(f"  结果 {i}:")
                    logger.info(f"    相关度: {score:.4f}")
                    logger.info(f"    内容预览: {text[:100]}...")
                    if metadata:
                        logger.info(f"    来源: {metadata.get('source', '未知')}")
            else:
                logger.warning(f"没有找到与 '{query}' 相关的结果")
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_threshold_settings():
    """测试阈值设置"""
    try:
        from vector_store import FaissVectorStore
        
        logger.info("=== 测试阈值设置 ===")
        
        vector_store = FaissVectorStore()
        
        logger.info(f"基础相似度阈值: {vector_store.similarity_threshold}")
        
        # 测试不同的查询
        test_query = "测试"
        logger.info(f"测试查询: '{test_query}'")
        
        # 临时调整阈值进行测试
        original_threshold = vector_store.similarity_threshold
        
        thresholds = [0.05, 0.1, 0.2, 0.3]
        for threshold in thresholds:
            vector_store.similarity_threshold = threshold
            results = vector_store.search(test_query, top_k=5)
            logger.info(f"阈值 {threshold}: 找到 {len(results)} 个结果")
        
        # 恢复原始阈值
        vector_store.similarity_threshold = original_threshold
        
    except Exception as e:
        logger.error(f"测试阈值设置时出错: {str(e)}")

def main():
    """主函数"""
    logger.info("开始搜索功能测试")
    
    # 测试搜索功能
    if test_search_functionality():
        logger.info("✓ 搜索功能测试完成")
    else:
        logger.error("✗ 搜索功能测试失败")
    
    # 测试阈值设置
    test_threshold_settings()
    
    logger.info("测试完成")

if __name__ == "__main__":
    main() 