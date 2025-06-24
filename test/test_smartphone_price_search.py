#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试智能手机价格搜索问题
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from vector_store import FaissVectorStore
from knowledge_query_service import KnowledgeQueryService, search_config
from config_loader import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_smartphone_price_search():
    """专门测试智能手机价格搜索"""
    try:
        logger.info("=" * 80)
        logger.info("专门测试智能手机价格搜索问题")
        logger.info("=" * 80)
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 加载数据
        if not vector_store.documents:
            vector_store.load("knowledge_base/vector_store")
        
        logger.info(f"向量存储中文档数量: {len(vector_store.documents)}")
        
        # 显示知识库内容
        logger.info("\n知识库内容预览:")
        logger.info("-" * 60)
        for i, (text, metadata) in enumerate(vector_store.documents):
            preview = text[:100] + "..." if len(text) > 100 else text
            logger.info(f"文档 {i+1}: {preview}")
            logger.info(f"来源: {metadata.get('source', '未知')}")
            logger.info("-" * 60)
        
        # 测试查询
        query = "智能手机价格多少"
        logger.info(f"\n测试查询: '{query}'")
        logger.info("=" * 60)
        
        # 1. 测试向量存储原始搜索
        logger.info("\n1. 向量存储原始搜索:")
        logger.info("-" * 40)
        results = vector_store.search(query, top_k=5)
        logger.info(f"找到 {len(results)} 个结果")
        
        for i, (text, score, metadata) in enumerate(results):
            debug_info = metadata.get('_debug_info', {})
            logger.info(f"结果 {i+1}:")
            logger.info(f"  分数: {score:.4f}")
            logger.info(f"  向量相似度: {debug_info.get('vector_similarity', 'N/A')}")
            logger.info(f"  关键词匹配: {debug_info.get('keyword_match', 'N/A')}")
            logger.info(f"  内容: {text[:80]}...")
            logger.info("-" * 40)
        
        # 2. 测试知识查询服务（微信配置）
        logger.info("\n2. 知识查询服务（微信配置）:")
        logger.info("-" * 40)
        query_service = KnowledgeQueryService(vector_store)
        wechat_result = query_service.search_for_wechat(query)
        
        logger.info(f"搜索成功: {wechat_result.get('success', False)}")
        logger.info(f"消息: {wechat_result.get('message', '无')}")
        results = wechat_result.get('results', [])
        logger.info(f"找到 {len(results)} 个结果")
        
        for i, item in enumerate(results):
            logger.info(f"结果 {i+1}:")
            logger.info(f"  分数: {item.get('score', 0):.4f}")
            logger.info(f"  内容: {item.get('content', '')[:80]}...")
            logger.info("-" * 40)
        
        # 3. 测试知识查询服务（Web配置）
        logger.info("\n3. 知识查询服务（Web配置）:")
        logger.info("-" * 40)
        web_result = query_service.search_for_web(query)
        
        logger.info(f"搜索成功: {web_result.get('success', False)}")
        logger.info(f"消息: {web_result.get('message', '无')}")
        results = web_result.get('results', [])
        logger.info(f"找到 {len(results)} 个结果")
        
        for i, item in enumerate(results):
            logger.info(f"结果 {i+1}:")
            logger.info(f"  分数: {item.get('score', 0):.4f}")
            logger.info(f"  内容: {item.get('content', '')[:80]}...")
            logger.info("-" * 40)
        
        # 4. 分析问题原因
        logger.info("\n4. 问题分析:")
        logger.info("-" * 40)
        
        # 检查配置
        logger.info(f"配置文件相似度阈值: {config.getfloat('vector_store', 'similarity_threshold', fallback=0.3)}")
        logger.info(f"向量存储相似度阈值: {vector_store.similarity_threshold}")
        logger.info(f"微信搜索最小分数: {search_config.wechat_min_score}")
        logger.info(f"Web搜索最小分数: {search_config.web_min_score}")
        
        # 分析关键词匹配
        if vector_store.documents:
            text, metadata = vector_store.documents[0]  # 取第一个文档
            keyword_match = vector_store.calculate_keyword_match(query, text)
            logger.info(f"查询'{query}'与文档的关键词匹配度: {keyword_match:.4f}")
            
            # 分词分析
            import jieba
            query_words = set(w for w in jieba.lcut_for_search(query) if len(w) > 1)
            text_words = set(w for w in jieba.lcut_for_search(text) if len(w) > 1)
            logger.info(f"查询分词: {query_words}")
            logger.info(f"文档分词: {text_words}")
            logger.info(f"匹配词汇: {query_words & text_words}")
        
        # 5. 提供解决方案
        logger.info("\n5. 解决方案:")
        logger.info("-" * 40)
        logger.info("问题原因: 向量存储内部的过滤条件过于严格")
        logger.info("解决方案:")
        logger.info("1. 降低向量存储的相似度阈值")
        logger.info("2. 降低关键词匹配阈值")
        logger.info("3. 降低加权分数阈值")
        logger.info("4. 或者调整权重分配")
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def fix_search_issue():
    """修复搜索问题"""
    try:
        logger.info("\n" + "=" * 80)
        logger.info("修复搜索问题")
        logger.info("=" * 80)
        
        # 方案1: 调整配置文件中的相似度阈值
        logger.info("\n方案1: 调整配置文件")
        logger.info("-" * 40)
        
        # 读取当前配置
        current_threshold = config.getfloat('vector_store', 'similarity_threshold', fallback=0.3)
        logger.info(f"当前相似度阈值: {current_threshold}")
        
        # 建议的新阈值
        new_threshold = 0.1
        logger.info(f"建议的新阈值: {new_threshold}")
        
        # 方案2: 修改向量存储的过滤条件
        logger.info("\n方案2: 修改向量存储过滤条件")
        logger.info("-" * 40)
        logger.info("需要修改 vector_store.py 中的过滤条件:")
        logger.info("- 降低关键词匹配阈值从 0.3 到 0.1")
        logger.info("- 降低加权分数阈值从 0.4 到 0.2")
        logger.info("- 或者完全移除这些过滤条件")
        
        # 方案3: 修改知识查询服务的配置
        logger.info("\n方案3: 修改知识查询服务配置")
        logger.info("-" * 40)
        logger.info("需要修改 knowledge_query_service.py 中的配置:")
        logger.info("- 降低微信搜索的最小分数阈值")
        logger.info("- 降低Web搜索的最小分数阈值")
        
        return True
        
    except Exception as e:
        logger.error(f"修复过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 运行测试
    test_smartphone_price_search()
    
    # 提供修复方案
    fix_search_issue() 