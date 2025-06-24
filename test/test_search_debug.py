#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试"智能手机价格"搜索问题
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from vector_store import FaissVectorStore
from knowledge_query_service import KnowledgeQueryService
import jieba

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_smartphone_price_search():
    """调试智能手机价格搜索问题"""
    try:
        logger.info("=" * 80)
        logger.info("调试智能手机价格搜索问题")
        logger.info("=" * 80)
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 加载数据
        if not vector_store.documents:
            vector_store.load("knowledge_base/vector_store")
        
        logger.info(f"向量存储中文档数量: {len(vector_store.documents)}")
        
        # 显示所有文档内容
        logger.info("\n所有文档内容:")
        logger.info("-" * 60)
        for i, (text, metadata) in enumerate(vector_store.documents):
            logger.info(f"文档 {i+1}: {text}")
            logger.info(f"来源: {metadata.get('source', '未知')}")
            logger.info("-" * 60)
        
        # 测试不同的查询
        test_queries = [
            "智能手机",
            "智能手机价格",
            "智能手机价格多少",
            "价格",
            "智能手表"
        ]
        
        for query in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"测试查询: '{query}'")
            logger.info(f"{'='*60}")
            
            # 分词分析
            query_words = set(w for w in jieba.lcut_for_search(query) if len(w) > 1)
            logger.info(f"查询分词: {query_words}")
            
            # 对每个文档计算关键词匹配
            logger.info("\n各文档的关键词匹配分析:")
            logger.info("-" * 60)
            
            for i, (text, metadata) in enumerate(vector_store.documents):
                # 计算关键词匹配
                keyword_match = vector_store.calculate_keyword_match(query, text)
                
                # 分词分析
                text_words = set(w for w in jieba.lcut_for_search(text) if len(w) > 1)
                matches = query_words & text_words
                
                logger.info(f"文档 {i+1}:")
                logger.info(f"  内容: {text[:80]}...")
                logger.info(f"  文档分词: {text_words}")
                logger.info(f"  匹配词汇: {matches}")
                logger.info(f"  关键词匹配度: {keyword_match:.4f}")
                logger.info("-" * 60)
            
            # 执行搜索
            logger.info(f"\n搜索结果:")
            logger.info("-" * 60)
            results = vector_store.search(query, top_k=5)
            
            for i, (text, score, metadata) in enumerate(results):
                debug_info = metadata.get('_debug_info', {})
                logger.info(f"结果 {i+1}:")
                logger.info(f"  分数: {score:.4f}")
                logger.info(f"  向量相似度: {debug_info.get('vector_similarity', 'N/A')}")
                logger.info(f"  关键词匹配: {debug_info.get('keyword_match', 'N/A')}")
                logger.info(f"  内容: {text[:80]}...")
                logger.info("-" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"调试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    debug_smartphone_price_search() 