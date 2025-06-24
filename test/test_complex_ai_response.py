#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试复杂的大模型返回JSON格式
"""

import json
import re
from ai_chunk_service import AIChunkService

def test_complex_ai_responses():
    """测试复杂的大模型返回JSON格式"""
    print("=== 测试复杂的大模型返回JSON格式 ===\n")
    
    # 初始化AI分块服务
    ai_service = AIChunkService()
    
    # 测试用例1：从日志中提取的实际AI响应
    test_json1 = '''```json
{
    "chunks": [
        {
            "content": "项目技术文档",
            "type": "标题",
            "reason": "文档总标题"
        },
        {
            "content": "第一章：项目背景 本项目旨在开发一个基于人工智能的知识管理系统，为用户提供智能化的文档管理和查询服务。",
            "type": "段落",
            "reason": "介绍项目的背景和目标"
        },
        {
            "content": "技术架构：",
            "type": "标题",
            "reason": "\"技术架构\"作为章节标题"
        },
        {
            "content": "- React.js: 用户界面框架  \n- Bootstrap: UI组件库  \n- Axios: HTTP客户端",
            "type": "列表项",
            "reason": "\"前端技术栈\"的技术细节"
        },
        {
            "content": "- Python Flask: Web框架  \n- FAISS: 向量数据库  \n- Sentence Transformers: 文本向量化",
            "type": "",
            reason": ""后端技术栈"的技术细节"
        },
        {
            content": "- 大语言模型API: 智能分块和问答  \n- 向量相似度搜索: 语义匹配  \n- 关键词提取: 内容分析",
            type": "列表项",
            reason": ""AI服务集成"的技术细节"
        },
        {
            content": "部署方案:",
            "type": "标题",
            "reason": ""部署方案"作为章节标题"
        },
        {
            "content": "一、开发环境 使用Docker容器化部署，支持快速开发和测试。",
            "type": "列表项",
            "reason": "描述开发环境的部署方案"
        },
        {
            "content": "二、生产环境 采用微服务架构，支持高并发和水平扩展。",
            "type": "列表项",
            "reason": "描述生产环境的部署方案"
        }
    ]
}
```'''
    
    print("测试用例1：从日志中提取的实际AI响应")
    result1 = ai_service._robust_json_parse(test_json1)
    if result1 and 'chunks' in result1:
        print(f"✓ 解析成功，包含 {len(result1['chunks'])} 个块")
        for i, chunk in enumerate(result1['chunks'][:3]):
            content = chunk.get('content', '')[:50] + '...' if len(chunk.get('content', '')) > 50 else chunk.get('content', '')
            print(f"  块 {i+1}: {content}")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：包含转义字符和特殊格式的JSON
    test_json2 = '''{
        "chunks": [
            {
                "content": "智能系统使用手册",
                "type": "标题",
                "reason": "作为整个文档的主标题"
            },
            {
                "content": "第一章：系统概述\\n\\n本智能系统是一款基于人工智能技术的知识管理平台，旨在帮助用户高效地管理和查询文档信息。",
                "type": "章节标题与段落",
                "reason": "这是章节标题及其后续描述段落，共同构成对系统的整体介绍。"
            },
            {
                "content": "\\n系统特点：\\n",
                "type": "子标题",
                "reason": "这是引入系统特点的具体描述部分的子标题。"
            },
            {
                "content": "\\n1. 智能文档处理\\n   支持多种文档格式，包括PDF、Word、Excel、TXT等。\\n   自动提取文档内容，生成结构化数据。",
                "type": "列表项",
                "reason": "这是第一个功能点及其详细说明，构成一个完整的功能描述单元。"
            }
        ]
    }'''
    
    print("测试用例2：包含转义字符和特殊格式的JSON")
    result2 = ai_service._robust_json_parse(test_json2)
    if result2 and 'chunks' in result2:
        print(f"✓ 解析成功，包含 {len(result2['chunks'])} 个块")
        for i, chunk in enumerate(result2['chunks'][:2]):
            content = chunk.get('content', '')[:50] + '...' if len(chunk.get('content', '')) > 50 else chunk.get('content', '')
            print(f"  块 {i+1}: {content}")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例3：极度混乱的JSON格式
    test_json3 = '''{
        "chunks": [
            {
                "content": "项目技术文档",
                "type": "标题",
                "reason": "文档总标题"
            },
            {
                content": "第一章：项目背景",
                type": "章节标题",
                reason": "章节起始标识"
            },
            {
                "content": "技术架构：",
                "type": "子标题",
                "reason": "小节标题"
            },
            {
                content": "部署方案：",
                "type": "标题",
                "reason": "部署方案标题"
            },
            {
                "content": "一、开发环境",
                "type": "列表项",
                "reason": "开发环境描述"
            }
        ]
    }'''
    
    print("测试用例3：极度混乱的JSON格式")
    result3 = ai_service._robust_json_parse(test_json3)
    if result3 and 'chunks' in result3:
        print(f"✓ 解析成功，包含 {len(result3['chunks'])} 个块")
        for i, chunk in enumerate(result3['chunks'][:3]):
            content = chunk.get('content', '')[:30] + '...' if len(chunk.get('content', '')) > 30 else chunk.get('content', '')
            print(f"  块 {i+1}: {content}")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例4：包含多余引号和格式错误的JSON
    test_json4 = '''```json
{
    "chunks": [
        {
            "content": "项目技术文档",
            "type": "标题",
            "reason": "文档总标题"
        },
        {
            ""content"": ""第一章：项目背景"",
            ""type"": ""章节标题"",
            ""reason"": ""章节起始标识""
        },
        {
            "content": "技术架构：",
            "type": "子标题",
            "reason": "小节标题"
        },
        {
            ""content"": ""部署方案："",
            ""type"": ""标题"",
            ""reason"": ""部署方案标题""
        }
    ]
}
```'''
    
    print("测试用例4：包含多余引号和格式错误的JSON")
    result4 = ai_service._robust_json_parse(test_json4)
    if result4 and 'chunks' in result4:
        print(f"✓ 解析成功，包含 {len(result4['chunks'])} 个块")
        for i, chunk in enumerate(result4['chunks'][:2]):
            content = chunk.get('content', '')[:30] + '...' if len(chunk.get('content', '')) > 30 else chunk.get('content', '')
            print(f"  块 {i+1}: {content}")
    else:
        print("✗ 解析失败")

def test_manual_parsing():
    """测试手动解析策略"""
    print("\n=== 测试手动解析策略 ===\n")
    
    ai_service = AIChunkService()
    
    # 测试手动解析策略
    test_json = '''{
        "chunks": [
            {
                "content": "项目技术文档",
                "type": "标题",
                "reason": "文档总标题"
            },
            {
                content": "第一章：项目背景",
                type": "章节标题",
                reason": "章节起始标识"
            }
        ]
    }'''
    
    print("测试手动解析策略")
    result = ai_service._strategy_manual_parse(test_json)
    if result and 'chunks' in result:
        print(f"✓ 手动解析成功，包含 {len(result['chunks'])} 个块")
        for i, chunk in enumerate(result['chunks']):
            content = chunk.get('content', '')[:30] + '...' if len(chunk.get('content', '')) > 30 else chunk.get('content', '')
            print(f"  块 {i+1}: {content}")
    else:
        print("✗ 手动解析失败")

if __name__ == "__main__":
    test_complex_ai_responses()
    test_manual_parsing() 