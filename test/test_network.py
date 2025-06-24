#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from config_loader import config

def test_ai_service_connection():
    """测试AI服务连接"""
    print("=== 测试AI服务连接 ===")
    
    try:
        # 获取配置
        api_url = config.get('api', 'url')
        api_key = config.get_secret('siliconflow_api_key')
        
        print(f"API URL: {api_url}")
        print(f"API Key: {api_key[:10]}...")
        
        # 测试模型列表接口
        print("\n1. 测试模型列表接口...")
        models_url = "https://api.siliconflow.cn/v1/models"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(models_url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ 模型列表接口连接成功")
            models = response.json()
            print(f"可用模型数量: {len(models.get('data', []))}")
            for model in models.get('data', [])[:3]:
                print(f"  - {model.get('id', 'N/A')}")
        else:
            print(f"✗ 模型列表接口连接失败: {response.text}")
        
        # 测试聊天接口
        print("\n2. 测试聊天接口...")
        chat_url = "https://api.siliconflow.cn/v1/chat/completions"
        data = {
            "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "messages": [
                {"role": "user", "content": "你好"}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        response = requests.post(chat_url, headers=headers, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ 聊天接口连接成功")
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"AI回复: {content}")
        else:
            print(f"✗ 聊天接口连接失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
    except requests.exceptions.ConnectionError:
        print("✗ 连接错误")
    except Exception as e:
        print(f"✗ 其他错误: {e}")

if __name__ == "__main__":
    test_ai_service_connection() 