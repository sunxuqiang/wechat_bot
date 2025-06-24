#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试知识库查询服务
"""

import os
import sys
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_knowledge_query_service():
    """测试知识库查询服务"""
    try:
        from knowledge_query_service import get_knowledge_query_service
        from vector_store import FaissVectorStore
        
        logger.info("=== 测试知识库查询服务 ===")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        
        # 加载向量存储
        vector_store_path = "knowledge_base/vector_store"
        if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
            vector_store.load(vector_store_path)
            logger.info(f"加载向量存储，共 {len(vector_store.documents)} 个文档")
        else:
            logger.error("向量存储文件不存在")
            return False
        
        # 获取知识库查询服务
        query_service = get_knowledge_query_service()
        query_service.set_vector_store(vector_store)
        
        # 测试基本搜索功能
        logger.info("\n--- 测试基本搜索功能 ---")
        test_queries = ["测试", "文档", "知识库", "搜索"]
        
        for query in test_queries:
            logger.info(f"\n查询: '{query}'")
            result = query_service.search_knowledge_base(query, top_k=3)
            
            if result['success']:
                logger.info(f"  成功，找到 {len(result['results'])} 个结果")
                for i, item in enumerate(result['results'][:2]):  # 只显示前2个
                    logger.info(f"    {i+1}. 分数: {item['score']:.4f}, 来源: {item['source']}")
            else:
                logger.info(f"  失败: {result['error']}")
        
        # 测试带上下文的搜索
        logger.info("\n--- 测试带上下文的搜索 ---")
        conversation_history = [
            {'role': 'user', 'content': '什么是知识库'},
            {'role': 'assistant', 'content': '知识库是一个存储知识的系统'},
            {'role': 'user', 'content': '它有什么功能'}
        ]
        pronouns = ['它', '这个', '那个']
        
        result = query_service.search_with_context(
            query='它有什么功能',
            user_id='test_user',
            conversation_history=conversation_history,
            pronouns=pronouns
        )
        
        if result['success']:
            logger.info(f"带上下文搜索成功")
            logger.info(f"  原始查询: '{result['query']}'")
            logger.info(f"  找到 {len(result['results'])} 个结果")
            if result['kb_context']:
                logger.info(f"  知识库上下文: {result['kb_context'][:200]}...")
        else:
            logger.info(f"带上下文搜索失败: {result['error']}")
        
        # 测试查询验证
        logger.info("\n--- 测试查询验证 ---")
        test_queries_validation = [
            ("", "空查询"),
            ("a", "短查询"),
            ("正常查询", "正常查询"),
            ("x" * 1001, "过长查询")
        ]
        
        for query, desc in test_queries_validation:
            is_valid, error_msg = query_service.validate_query(query)
            logger.info(f"  {desc}: {'有效' if is_valid else f'无效 ({error_msg})'}")
        
        # 测试统计信息
        logger.info("\n--- 测试统计信息 ---")
        stats = query_service.get_search_statistics()
        if stats['success']:
            logger.info(f"统计信息获取成功")
            for key, value in stats['statistics'].items():
                logger.info(f"  {key}: {value}")
        else:
            logger.info(f"统计信息获取失败: {stats['error']}")
        
        logger.info("\n✓ 知识库查询服务测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """测试API集成"""
    try:
        logger.info("\n=== 测试API集成 ===")
        
        # 模拟API调用
        from knowledge_query_service import get_knowledge_query_service
        from vector_store import FaissVectorStore
        
        # 初始化
        vector_store = FaissVectorStore()
        vector_store_path = "knowledge_base/vector_store"
        if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
            vector_store.load(vector_store_path)
        
        query_service = get_knowledge_query_service()
        query_service.set_vector_store(vector_store)
        
        # 模拟app.py的搜索API
        query = "测试"
        search_result = query_service.search_knowledge_base(
            query=query, 
            top_k=10,
            include_metadata=True
        )
        
        if search_result['success']:
            formatted_results = query_service.format_results_for_api(search_result['results'])
            logger.info(f"API格式结果: {len(formatted_results)} 个")
            for i, result in enumerate(formatted_results[:2]):
                logger.info(f"  {i+1}. content: {result['content'][:50]}..., score: {result['score']:.4f}")
        else:
            logger.error(f"API搜索失败: {search_result['error']}")
        
        # 模拟wechat_bot.py的上下文搜索
        conversation_history = [
            {'role': 'user', 'content': '什么是知识库'},
            {'role': 'assistant', 'content': '知识库是一个存储知识的系统'},
            {'role': 'user', 'content': '它有什么功能'}
        ]
        pronouns = ['它', '这个', '那个']
        
        context_result = query_service.search_with_context(
            query='它有什么功能',
            user_id='test_user',
            conversation_history=conversation_history,
            pronouns=pronouns
        )
        
        if context_result['success']:
            logger.info(f"上下文搜索成功，kb_context长度: {len(context_result['kb_context']) if context_result['kb_context'] else 0}")
        else:
            logger.error(f"上下文搜索失败: {context_result['error']}")
        
        logger.info("✓ API集成测试完成")
        return True
        
    except Exception as e:
        logger.error(f"API集成测试中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始测试知识库查询服务")
    
    # 测试知识库查询服务
    if test_knowledge_query_service():
        logger.info("✓ 知识库查询服务测试通过")
    else:
        logger.error("✗ 知识库查询服务测试失败")
        return
    
    # 测试API集成
    if test_api_integration():
        logger.info("✓ API集成测试通过")
    else:
        logger.error("✗ API集成测试失败")
    
    logger.info("所有测试完成")

if __name__ == "__main__":
    main() 