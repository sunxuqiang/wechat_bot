#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试智能手机文档被过滤的原因
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from vector_store import FaissVectorStore
import jieba

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_smartphone_filter():
    """详细调试智能手机文档被过滤的原因"""
    try:
        logger.info("=" * 80)
        logger.info("详细调试智能手机文档被过滤的原因")
        logger.info("=" * 80)
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 加载数据
        if not vector_store.documents:
            vector_store.load("knowledge_base/vector_store")
        
        # 测试查询
        query = "智能手机价格"
        logger.info(f"测试查询: '{query}'")
        
        # 找到智能手机文档
        smartphone_doc = None
        smartphone_index = None
        
        for i, (text, metadata) in enumerate(vector_store.documents):
            if "智能手机" in text:
                smartphone_doc = (text, metadata)
                smartphone_index = i
                break
        
        if not smartphone_doc:
            logger.error("未找到智能手机文档")
            return False
        
        text, metadata = smartphone_doc
        logger.info(f"智能手机文档索引: {smartphone_index}")
        logger.info(f"智能手机文档内容: {text}")
        
        # 生成查询向量
        query_vector = vector_store.encode_text(query)
        query_vector = vector_store.normalize_vector(query_vector)
        
        # 获取文档向量
        doc_vector = vector_store.document_embeddings[smartphone_index]
        doc_vector = vector_store.normalize_vector(doc_vector)
        
        # 计算各项指标
        vector_similarity = vector_store.cosine_similarity(query_vector, doc_vector)
        keyword_match = vector_store.calculate_keyword_match(query, text)
        weighted_score = 0.4 * vector_similarity + 0.6 * keyword_match
        
        logger.info("\n详细计算结果:")
        logger.info("-" * 60)
        logger.info(f"向量相似度: {vector_similarity:.4f}")
        logger.info(f"关键词匹配度: {keyword_match:.4f}")
        logger.info(f"加权分数: {weighted_score:.4f}")
        logger.info("-" * 60)
        
        # 检查过滤条件
        logger.info("\n过滤条件检查:")
        logger.info("-" * 60)
        logger.info(f"向量相似度阈值: {vector_store.similarity_threshold}")
        logger.info(f"关键词匹配阈值: 0.1")
        logger.info(f"加权分数阈值: 0.2")
        logger.info("-" * 60)
        
        condition1 = vector_similarity >= vector_store.similarity_threshold
        condition2 = keyword_match >= 0.1
        condition3 = weighted_score >= 0.2
        
        logger.info(f"条件1 (向量相似度 >= {vector_store.similarity_threshold}): {condition1}")
        logger.info(f"条件2 (关键词匹配 >= 0.1): {condition2}")
        logger.info(f"条件3 (加权分数 >= 0.2): {condition3}")
        
        if condition1 and condition2 and condition3:
            logger.info("✓ 所有条件都满足，文档应该被包含在结果中")
        else:
            logger.info("✗ 有条件不满足，文档被过滤掉")
            if not condition1:
                logger.info(f"  原因: 向量相似度 {vector_similarity:.4f} < {vector_store.similarity_threshold}")
            if not condition2:
                logger.info(f"  原因: 关键词匹配 {keyword_match:.4f} < 0.1")
            if not condition3:
                logger.info(f"  原因: 加权分数 {weighted_score:.4f} < 0.2")
        
        # 分词分析
        logger.info("\n分词分析:")
        logger.info("-" * 60)
        query_words = set(w for w in jieba.lcut_for_search(query) if len(w) > 1)
        text_words = set(w for w in jieba.lcut_for_search(text) if len(w) > 1)
        matches = query_words & text_words
        
        logger.info(f"查询分词: {query_words}")
        logger.info(f"文档分词: {text_words}")
        logger.info(f"匹配词汇: {matches}")
        logger.info(f"匹配率: {len(matches)}/{len(query_words)} = {len(matches)/len(query_words):.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"调试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    debug_smartphone_filter() 