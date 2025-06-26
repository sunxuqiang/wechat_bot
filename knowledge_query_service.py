#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库查询服务类
统一管理知识库查询功能，避免代码重复和不一致问题
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import traceback
from config_loader import config
from pathlib import Path

logger = logging.getLogger(__name__)

class SearchConfig:
    """搜索配置类，统一管理所有搜索参数"""
    
    def __init__(self):
        """初始化搜索配置"""
        # 从配置文件加载默认值
        self.max_results = config.getint('vector_store', 'max_results', fallback=5)
        self.min_score = config.getfloat('vector_store', 'similarity_threshold', fallback=0.3)
        self.top_k = config.getint('vector_store', 'max_results', fallback=5)
        
        # 微信机器人专用配置
        self.wechat_max_results = 10  # 微信机器人默认返回10个结果
        self.wechat_min_score = 0.3  # 微信机器人默认最小分数
        
        # Web界面专用配置
        self.web_max_results = 10    # Web界面默认返回10个结果
        self.web_min_score = 0.3     # Web界面默认最小分数
        
    def get_wechat_config(self) -> Tuple[int, float]:
        """获取微信机器人搜索配置"""
        return self.wechat_max_results, self.wechat_min_score
    
    def get_web_config(self) -> Tuple[int, float]:
        """获取Web界面搜索配置"""
        return self.web_max_results, self.web_min_score
    
    def get_default_config(self) -> Tuple[int, float]:
        """获取默认搜索配置"""
        return self.max_results, self.min_score
    
    def update_config(self, max_results: int = None, min_score: float = None):
        """更新配置"""
        if max_results is not None:
            self.max_results = max_results
        if min_score is not None:
            self.min_score = min_score

# 全局搜索配置实例
search_config = SearchConfig()

class KnowledgeQueryService:
    """知识库查询服务类"""
    
    def __init__(self, vector_store=None):
        """
        初始化知识库查询服务
        
        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store
        self.search_config = search_config
        
    def set_vector_store(self, vector_store):
        """设置向量存储实例"""
        self.vector_store = vector_store
        
    def search_knowledge_base(self, query: str, top_k: int = None, 
                            min_score: float = None, 
                            include_metadata: bool = True,
                            search_type: str = 'default') -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            min_score: 最小分数阈值
            include_metadata: 是否包含元数据
            search_type: 搜索类型 ('wechat', 'web', 'default')
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            if not self.vector_store:
                logger.error("向量存储未初始化")
                return self._create_error_response("向量存储未初始化")
                
            if not query or len(query.strip()) < 2:
                logger.warning("查询内容过短")
                return self._create_error_response("查询内容过短")
            
            # 根据搜索类型获取默认配置
            if search_type == 'wechat':
                default_top_k, default_min_score = self.search_config.get_wechat_config()
            elif search_type == 'web':
                default_top_k, default_min_score = self.search_config.get_web_config()
            else:
                default_top_k, default_min_score = self.search_config.get_default_config()
            
            # 使用参数或默认值
            top_k = top_k or default_top_k
            min_score = min_score or default_min_score
            
            logger.info(f"开始搜索知识库: '{query}' (top_k={top_k}, min_score={min_score}, type={search_type})")
            
            # 执行搜索
            results = self.vector_store.search(query, top_k=top_k)
            
            if not results:
                logger.info("未找到相关结果")
                return self._create_success_response([], "未找到相关内容")
            
            # 过滤和格式化结果
            formatted_results = []
            for text, score, metadata in results:
                if score >= min_score:
                    result_item = {
                        'content': text,
                        'score': float(score),
                        'source': metadata.get('source', '未知'),
                        'filename': metadata.get('filename', '未知'),
                        'created_at': metadata.get('created_at', '未知')
                    }
                    
                    if include_metadata:
                        result_item['metadata'] = metadata
                        
                    formatted_results.append(result_item)
            
            logger.info(f"找到 {len(formatted_results)} 个相关结果")
            return self._create_success_response(formatted_results, "搜索成功")
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {str(e)}")
            logger.error(traceback.format_exc())
            return self._create_error_response(f"搜索失败: {str(e)}")
    
    def search_for_wechat(self, query: str, top_k: int = None, min_score: float = None, include_metadata: bool = True) -> Dict[str, Any]:
        """
        微信机器人专用搜索方法
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            min_score: 最小分数阈值
            include_metadata: 是否包含元数据
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        return self.search_knowledge_base(query, top_k, min_score, include_metadata, search_type='wechat')
    
    def search_for_web(self, query: str, top_k: int = None, min_score: float = None, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Web界面专用搜索方法
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            min_score: 最小分数阈值
            include_metadata: 是否包含元数据
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        return self.search_knowledge_base(query, top_k, min_score, include_metadata, search_type='web')
    
    def search_with_context(self, query: str, user_id: str = None, 
                          conversation_history: List[Dict] = None,
                          pronouns: List[str] = None) -> Dict[str, Any]:
        """
        带上下文的搜索（用于微信机器人）
        
        Args:
            query: 查询字符串
            user_id: 用户ID
            conversation_history: 对话历史
            pronouns: 指代词列表
            
        Returns:
            Dict[str, Any]: 搜索结果和上下文信息
        """
        try:
            # 构建搜索查询
            search_query = query
            
            # 如果包含指代词且有对话历史，尝试从历史中提取上下文
            if pronouns and conversation_history:
                if any(word in query for word in pronouns):
                    # 从最近的用户消息中提取关键词
                    for msg in reversed(conversation_history):
                        if msg.get('role') == 'user':
                            search_query = msg.get('content', query)
                            logger.info(f"使用历史上下文: '{search_query}'")
                            break
            
            # 执行搜索（使用微信专用配置）
            search_result = self.search_for_wechat(search_query)
            
            if search_result['success']:
                # 构建知识库上下文
                kb_context = None
                if search_result['results']:
                    context_parts = []
                    for result in search_result['results']:
                        context_parts.append(f"相关度{result['score']:.4f}: {result['content']}")
                    kb_context = "\n\n".join(context_parts)
                
                return {
                    'success': True,
                    'query': search_query,
                    'results': search_result['results'],
                    'kb_context': kb_context,
                    'message': search_result['message']
                }
            else:
                return search_result
                
        except Exception as e:
            logger.error(f"带上下文搜索失败: {str(e)}")
            logger.error(traceback.format_exc())
            return self._create_error_response(f"搜索失败: {str(e)}")
    
    def format_results_for_api(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化结果为API响应格式
        
        Args:
            results: 搜索结果列表
            
        Returns:
            List[Dict[str, Any]]: 格式化后的结果
        """
        formatted = []
        for result in results:
            formatted.append({
                'content': result['content'],
                'score': result['score'],
                'metadata': result.get('metadata', {})
            })
        return formatted
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        获取搜索统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            if not self.vector_store:
                return {'error': '向量存储未初始化'}
            
            stats = self.vector_store.get_statistics()
            return {
                'success': True,
                'statistics': stats
            }
        except Exception as e:
            logger.error(f"获取搜索统计信息失败: {str(e)}")
            return {'error': str(e)}
    
    def _create_success_response(self, results: List[Dict[str, Any]], message: str) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            'success': True,
            'results': results,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'success': False,
            'error': error_message,
            'results': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        验证查询参数
        
        Args:
            query: 查询字符串
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not query:
            return False, "查询内容不能为空"
        
        if len(query.strip()) < 2:
            return False, "查询内容至少需要2个字符"
        
        if len(query) > 1000:
            return False, "查询内容过长"
        
        return True, ""

# 全局实例
knowledge_query_service = KnowledgeQueryService()

def get_knowledge_query_service() -> KnowledgeQueryService:
    """获取知识库查询服务实例"""
    # 如果全局实例没有向量存储，尝试初始化
    if not knowledge_query_service.vector_store:
        try:
            from vector_store import FaissVectorStore
            vector_store = FaissVectorStore()
            vector_store_path = "knowledge_base/vector_store"
            
            # 检查向量存储文件是否存在
            index_file = Path(f"{vector_store_path}.index")
            pkl_file = Path(f"{vector_store_path}.pkl")
            
            if index_file.exists() and pkl_file.exists():
                vector_store.load(vector_store_path)
                knowledge_query_service.set_vector_store(vector_store)
                logger.info("全局知识库查询服务向量存储已初始化")
            else:
                logger.warning("向量存储文件不存在，无法初始化全局查询服务")
        except Exception as e:
            logger.error(f"初始化全局查询服务向量存储失败: {str(e)}")
    
    return knowledge_query_service 