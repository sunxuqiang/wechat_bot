#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import json
from config_loader import config

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_ai_response():
    """测试AI响应内容"""
    print("=== 测试AI响应内容 ===")
    
    # 测试文本
    test_text = """第一章：项目背景
本项目旨在开发一个基于人工智能的知识管理系统，为用户提供智能化的文档管理和查询服务。

技术架构：
1. 前端技术栈
   - React.js：用户界面框架
   - Bootstrap：UI组件库
   - Axios：HTTP客户端

2. 后端技术栈
   - Python Flask：Web框架
   - FAISS：向量数据库
   - Sentence Transformers：文本向量化

3. AI服务集成
   - 大语言模型API：智能分块和问答
   - 向量相似度搜索：语义匹配
   - 关键词提取：内容分析

部署方案：
一、开发环境
使用Docker容器化部署，支持快速开发和测试。"""
    
    print(f"测试文本长度: {len(test_text)} 字符")
    
    try:
        # 获取配置
        api_url = config.get('api', 'url')
        api_key = config.get_secret('siliconflow_api_key')
        
        # 构建请求
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        # 构建提示词
        prompt = f"""请将以下文本按语义分成几个块，每个块100-400字符。返回JSON格式：

{{
    "chunks": [
        {{"content": "文本块内容"}}
    ]
}}

文本：{test_text}"""
        
        data = {
            'model': 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 512,
            'temperature': 0.7
        }
        
        print("发送请求到AI服务...")
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            print(f"AI响应内容长度: {len(content)} 字符")
            print(f"AI响应内容:")
            print("=" * 50)
            print(content)
            print("=" * 50)
            
            # 尝试解析JSON
            try:
                import pyjson5
                parsed = pyjson5.decode(content)
                print(f"解析成功: {parsed}")
                
                chunks = parsed.get('chunks', [])
                print(f"chunks数量: {len(chunks)}")
                for i, chunk in enumerate(chunks):
                    print(f"块 {i+1}: {chunk}")
                    
            except Exception as e:
                print(f"JSON解析失败: {e}")
                
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_response() 