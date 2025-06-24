#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import config
from ai_chunk_service import AIChunkService

def test_config_reading():
    """测试配置读取"""
    print("=== 测试配置读取 ===")
    
    # 1. 直接读取配置文件
    print(f"配置文件中的 ai_chunking_model: {config.get('api', 'ai_chunking_model')}")
    print(f"配置文件中的 model: {config.get('api', 'model')}")
    
    # 2. 创建AI分块服务实例
    print("\n=== 创建AI分块服务实例 ===")
    ai_service = AIChunkService()
    print(f"AI分块服务中的 model: {ai_service.model}")
    print(f"AI分块服务中的 max_tokens: {ai_service.max_tokens}")
    print(f"AI分块服务中的 temperature: {ai_service.temperature}")
    
    # 3. 检查是否有其他可能的模型设置
    print("\n=== 检查其他可能的模型设置 ===")
    print(f"API URL: {ai_service.api_url}")
    print(f"API Key: {ai_service.api_key[:10]}..." if ai_service.api_key else "None")

if __name__ == "__main__":
    test_config_reading() 