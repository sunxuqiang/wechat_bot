#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理服务
统一管理系统中所有提示词，支持从配置文件读取和动态更新
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config_loader import config

logger = logging.getLogger(__name__)

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        """初始化提示词管理器"""
        self._prompts = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """从配置文件加载提示词"""
        try:
            # 加载基础系统提示词
            self._prompts['system_prompt'] = config.get('chat', 'system_prompt', fallback='')
            
            # 加载微信专用系统提示词
            self._prompts['wechat_system_prompt'] = config.get('chat', 'wechat_system_prompt', fallback='')
            
            # 加载用户提示词模板
            self._prompts['user_prompt_template'] = config.get('chat', 'user_prompt_template', fallback='')
            
            # 加载AI分块提示词
            self._load_ai_chunking_prompt()
            
            logger.info("提示词加载完成")
            
        except Exception as e:
            logger.error(f"加载提示词失败: {str(e)}")
            self._load_default_prompts()
    
    def _load_ai_chunking_prompt(self):
        """加载AI分块提示词"""
        try:
            prompt_file_path = config.get('api', 'ai_chunking_prompt_file', fallback='prompts/ai_chunking_prompt.txt')
            
            if os.path.exists(prompt_file_path):
                with open(prompt_file_path, 'r', encoding='utf-8') as f:
                    self._prompts['ai_chunking_prompt'] = f.read().strip()
            else:
                logger.warning(f"AI分块提示词文件不存在: {prompt_file_path}")
                self._prompts['ai_chunking_prompt'] = self._get_default_ai_chunking_prompt()
                
        except Exception as e:
            logger.error(f"加载AI分块提示词失败: {str(e)}")
            self._prompts['ai_chunking_prompt'] = self._get_default_ai_chunking_prompt()
    
    def _load_default_prompts(self):
        """加载默认提示词"""
        self._prompts = {
            'system_prompt': '你是一个专业、友好的AI助手。请基于提供的相关信息回答用户的问题。',
            'wechat_system_prompt': '你是一个专业、友好的AI助手。请基于提供的相关信息回答用户的问题。',
            'user_prompt_template': '用户问题：{message}\n\n请回答。',
            'ai_chunking_prompt': self._get_default_ai_chunking_prompt()
        }
    
    def _get_default_ai_chunking_prompt(self) -> str:
        """获取默认AI分块提示词"""
        return """你是一个专业的文档分块专家。请将以下文本按照章节结构进行智能分块。

请严格按照以下JSON格式返回：
{{
    "chunks": [
        {{
            "content": "章节内容",
            "type": "章节类型",
            "summary": "章节摘要"
        }}
    ]
}}

待分块文本：
{text}"""
    
    def get_prompt(self, prompt_name: str) -> str:
        """
        获取指定提示词
        
        Args:
            prompt_name: 提示词名称
            
        Returns:
            str: 提示词内容
        """
        return self._prompts.get(prompt_name, '')
    
    def get_system_prompt(self, prompt_type: str = 'default') -> str:
        """
        获取系统提示词
        
        Args:
            prompt_type: 提示词类型 ('default' 或 'wechat')
            
        Returns:
            str: 系统提示词
        """
        if prompt_type == 'wechat':
            return self._prompts.get('wechat_system_prompt', '')
        else:
            return self._prompts.get('system_prompt', '')
    
    def get_user_prompt_template(self) -> str:
        """
        获取用户提示词模板
        
        Returns:
            str: 用户提示词模板
        """
        return self._prompts.get('user_prompt_template', '')
    
    def get_ai_chunking_prompt(self) -> str:
        """
        获取AI分块提示词
        
        Returns:
            str: AI分块提示词
        """
        return self._prompts.get('ai_chunking_prompt', '')
    
    def format_user_prompt(self, message: str, context: str = '', history: str = '') -> str:
        """
        格式化用户提示词
        
        Args:
            message: 用户消息
            context: 知识库上下文
            history: 对话历史
            
        Returns:
            str: 格式化后的用户提示词
        """
        template = self.get_user_prompt_template()
        
        # 处理历史对话
        if not history:
            history = "无"
        
        # 处理知识库上下文
        if not context:
            context = "无相关信息"
        
        try:
            return template.format(
                message=message,
                context=context,
                history=history
            )
        except Exception as e:
            logger.error(f"格式化用户提示词失败: {str(e)}")
            # 返回简化版本
            return f"用户问题：{message}\n\n请回答。"
    
    def update_prompt(self, prompt_name: str, content: str) -> bool:
        """
        更新提示词
        
        Args:
            prompt_name: 提示词名称
            content: 提示词内容
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if prompt_name == 'ai_chunking_prompt':
                # 保存到文件
                prompt_file_path = config.get('api', 'ai_chunking_prompt_file', fallback='prompts/ai_chunking_prompt.txt')
                os.makedirs(os.path.dirname(prompt_file_path), exist_ok=True)
                
                with open(prompt_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"AI分块提示词已保存到: {prompt_file_path}")
            
            # 更新内存中的提示词
            self._prompts[prompt_name] = content
            return True
            
        except Exception as e:
            logger.error(f"更新提示词失败: {str(e)}")
            return False
    
    def reload_prompts(self) -> bool:
        """
        重新加载提示词
        
        Returns:
            bool: 是否重新加载成功
        """
        try:
            self._load_prompts()
            return True
        except Exception as e:
            logger.error(f"重新加载提示词失败: {str(e)}")
            return False
    
    def get_all_prompts(self) -> Dict[str, str]:
        """
        获取所有提示词
        
        Returns:
            Dict[str, str]: 所有提示词
        """
        return self._prompts.copy()
    
    def validate_prompt(self, prompt_name: str, content: str) -> Tuple[bool, str]:
        """
        验证提示词
        
        Args:
            prompt_name: 提示词名称
            content: 提示词内容
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not content.strip():
            return False, "提示词内容不能为空"
        
        if prompt_name == 'ai_chunking_prompt' and '{text}' not in content:
            return False, "AI分块提示词必须包含 {text} 占位符"
        
        if prompt_name == 'user_prompt_template':
            required_vars = ['{message}', '{context}', '{history}']
            missing_vars = [var for var in required_vars if var not in content]
            if missing_vars:
                return False, f"用户提示词模板缺少必要变量: {', '.join(missing_vars)}"
        
        return True, ""

# 全局提示词管理器实例
prompt_manager = PromptManager()

def get_prompt_manager() -> PromptManager:
    """获取提示词管理器实例"""
    return prompt_manager 