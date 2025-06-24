#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import config
from ai_chunk_service import AIChunkService

def test_prompt_config():
    """测试提示词配置"""
    print("=== 测试提示词配置 ===")
    
    # 1. 直接读取配置文件
    print(f"配置文件中的 ai_chunking_prompt: {config.get('api', 'ai_chunking_prompt', fallback='未配置')[:100]}...")
    
    # 2. 创建AI分块服务实例
    print("\n=== 创建AI分块服务实例 ===")
    ai_service = AIChunkService()
    print(f"AI分块服务中的 chunk_prompt: {ai_service.chunk_prompt[:100]}...")
    
    # 3. 测试提示词格式化
    print("\n=== 测试提示词格式化 ===")
    test_text = "这是一个测试文档。\n\n第一章：测试章节\n这是第一章的内容。"
    formatted_prompt = ai_service.chunk_prompt.format(text=test_text)
    print(f"格式化后的提示词长度: {len(formatted_prompt)} 字符")
    print(f"格式化后的提示词前200字符: {formatted_prompt[:200]}...")
    
    # 4. 验证占位符
    print("\n=== 验证占位符 ===")
    if '{text}' in ai_service.chunk_prompt:
        print("✓ 提示词包含 {text} 占位符")
    else:
        print("✗ 提示词缺少 {text} 占位符")
    
    # 5. 验证JSON格式要求
    print("\n=== 验证JSON格式要求 ===")
    if 'JSON' in ai_service.chunk_prompt and 'chunks' in ai_service.chunk_prompt:
        print("✓ 提示词包含JSON格式要求")
    else:
        print("✗ 提示词缺少JSON格式要求")

if __name__ == "__main__":
    test_prompt_config() 