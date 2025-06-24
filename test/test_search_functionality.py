#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索功能是否正常工作
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
from config_loader import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_search_functionality():
    """测试搜索功能"""
    try:
        logger.info("=" * 60)
        logger.info("开始测试搜索功能")
        logger.info("=" * 60)
        
        # 初始化向量存储
        logger.info("初始化向量存储...")
        vector_store = FaissVectorStore()
        
        # 检查向量存储是否已加载数据
        if not vector_store.documents:
            logger.info("尝试加载向量存储数据...")
            # 尝试从不同路径加载
            possible_paths = [
                "knowledge_base/vector_store",
                "data/vector_store",
                "vector_store"
            ]
            
            loaded = False
            for path in possible_paths:
                if os.path.exists(f"{path}.pkl") and os.path.exists(f"{path}.index"):
                    try:
                        vector_store.load(path)
                        logger.info(f"成功从 {path} 加载向量存储")
                        loaded = True
                        break
                    except Exception as e:
                        logger.warning(f"从 {path} 加载失败: {e}")
                        continue
            
            if not loaded:
                logger.error("无法加载向量存储数据")
                return False
        
        logger.info(f"向量存储中文档数量: {len(vector_store.documents)}")
        
        # 显示知识库中的文档内容预览
        logger.info("\n知识库文档内容预览:")
        logger.info("-" * 60)
        for i, (text, metadata) in enumerate(vector_store.documents[:3]):  # 只显示前3个
            preview = text[:100] + "..." if len(text) > 100 else text
            logger.info(f"文档 {i+1}: {preview}")
            logger.info(f"来源: {metadata.get('source', '未知')}")
            logger.info("-" * 60)
        
        # 初始化知识查询服务
        query_service = KnowledgeQueryService(vector_store)
        
        # 测试不同的查询
        test_queries = [
            "智能手机价格多少",  # 原始查询
            "智能系统",         # 应该能找到相关内容
            "文档管理",         # 应该能找到相关内容
            "安装配置",         # 应该能找到相关内容
            "技术支持",         # 应该能找到相关内容
            "系统要求",         # 应该能找到相关内容
            "搜索功能",         # 应该能找到相关内容
        ]
        
        logger.info("\n开始测试不同查询:")
        logger.info("=" * 80)
        
        for query in test_queries:
            logger.info(f"\n测试查询: '{query}'")
            logger.info("-" * 40)
            
            # 使用微信配置测试
            result_wechat = query_service.search_for_wechat(query)
            logger.info(f"微信搜索结果: {result_wechat.get('success', False)}")
            if result_wechat.get('success'):
                results = result_wechat.get('data', [])
                logger.info(f"找到 {len(results)} 个结果")
                for i, item in enumerate(results[:2]):  # 只显示前2个结果
                    logger.info(f"  结果 {i+1}: 分数={item.get('score', 0):.4f}")
                    logger.info(f"    内容: {item.get('content', '')[:80]}...")
            else:
                logger.info(f"微信搜索失败: {result_wechat.get('message', '未知错误')}")
            
            # 使用Web配置测试
            result_web = query_service.search_for_web(query)
            logger.info(f"Web搜索结果: {result_web.get('success', False)}")
            if result_web.get('success'):
                results = result_web.get('data', [])
                logger.info(f"找到 {len(results)} 个结果")
                for i, item in enumerate(results[:2]):  # 只显示前2个结果
                    logger.info(f"  结果 {i+1}: 分数={item.get('score', 0):.4f}")
                    logger.info(f"    内容: {item.get('content', '')[:80]}...")
            else:
                logger.info(f"Web搜索失败: {result_web.get('message', '未知错误')}")
            
            logger.info("-" * 40)
        
        # 测试向量存储的原始搜索方法
        logger.info("\n测试向量存储原始搜索方法:")
        logger.info("=" * 60)
        
        for query in ["智能系统", "文档管理", "智能手机价格"]:
            logger.info(f"\n原始搜索: '{query}'")
            results = vector_store.search(query, top_k=3)
            logger.info(f"找到 {len(results)} 个结果")
            for i, (text, score, metadata) in enumerate(results):
                debug_info = metadata.get('_debug_info', {})
                logger.info(f"  结果 {i+1}: 分数={score:.4f}")
                logger.info(f"    向量相似度: {debug_info.get('vector_similarity', 'N/A')}")
                logger.info(f"    关键词匹配: {debug_info.get('keyword_match', 'N/A')}")
                logger.info(f"    内容: {text[:80]}...")
        
        logger.info("\n" + "=" * 60)
        logger.info("搜索功能测试完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def analyze_search_issue():
    """分析搜索问题的根本原因"""
    logger.info("\n" + "=" * 60)
    logger.info("分析搜索问题根本原因")
    logger.info("=" * 60)
    
    # 检查配置文件中的相似度阈值
    similarity_threshold = config.getfloat('vector_store', 'similarity_threshold', fallback=0.3)
    logger.info(f"配置文件中的相似度阈值: {similarity_threshold}")
    
    # 检查向量存储中的相似度阈值
    vector_store = FaissVectorStore()
    logger.info(f"向量存储中的相似度阈值: {vector_store.similarity_threshold}")
    
    # 检查搜索配置
    from knowledge_query_service import search_config
    logger.info(f"微信搜索配置: max_results={search_config.wechat_max_results}, min_score={search_config.wechat_min_score}")
    logger.info(f"Web搜索配置: max_results={search_config.web_max_results}, min_score={search_config.web_min_score}")
    
    logger.info("\n问题分析:")
    logger.info("1. 知识库中的文档内容是关于'智能系统使用手册'的")
    logger.info("2. 查询'智能手机价格多少'与文档内容不匹配")
    logger.info("3. 搜索算法使用了严格的过滤条件:")
    logger.info("   - 向量相似度必须 >= 0.3")
    logger.info("   - 关键词匹配必须 >= 0.3")
    logger.info("   - 加权分数必须 >= 0.4")
    logger.info("4. 对于不相关的内容，这些条件都无法满足")
    
    logger.info("\n解决方案建议:")
    logger.info("1. 上传包含智能手机价格信息的文档")
    logger.info("2. 或者调整搜索参数，降低阈值（但可能影响搜索质量）")
    logger.info("3. 或者使用更相关的查询词，如'智能系统'、'文档管理'等")

if __name__ == "__main__":
    # 运行搜索功能测试
    test_search_functionality()
    
    # 分析问题原因
    analyze_search_issue() 