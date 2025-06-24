#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试强大的JSON解析功能
"""

import json
import re
from ai_chunk_service import AIChunkService

def test_robust_json_parse():
    """测试强大的JSON解析功能"""
    print("=== 测试强大的JSON解析功能 ===\n")
    
    # 初始化AI分块服务
    ai_service = AIChunkService()
    
    # 测试用例1：标准JSON
    test_json1 = '''{
        "chunks": [
            {
                "content": "项目技术文档",
                "type": "标题",
                "reason": "文档总标题"
            },
            {
                "content": "第一章：项目背景",
                "type": "章节标题",
                "reason": "章节起始标识"
            }
        ]
    }'''
    
    print("测试用例1：标准JSON")
    result1 = ai_service._robust_json_parse(test_json1)
    if result1 and 'chunks' in result1:
        print(f"✓ 解析成功，包含 {len(result1['chunks'])} 个块")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：缺少引号的JSON
    test_json2 = '''{
        "chunks": [
            {
                content: "项目技术文档",
                type: "标题",
                reason: "文档总标题"
            },
            {
                content: "第一章：项目背景",
                type: "章节标题",
                reason: "章节起始标识"
            }
        ]
    }'''
    
    print("测试用例2：缺少引号的JSON")
    result2 = ai_service._robust_json_parse(test_json2)
    if result2 and 'chunks' in result2:
        print(f"✓ 解析成功，包含 {len(result2['chunks'])} 个块")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例3：复杂的实际AI响应
    test_json3 = '''```json
{
    "chunks": [
        {
            "content": "项目技术文档",
            "type": "标题",
            "reason": "文档总标题"
        },
        {
            "content": "第一章：项目背景\n本项目旨在开发一个基于人工智能的知识管理系统，为用户提供智能化的文档管理和查询服务。",
            "type": "章节标题",
            "reason": "章节标题及对应段落"
        },
        {
            "content": "技术架构：",
            "type": "子标题",
            "reason": "小节标题"
        },
        {
            "content": "- React.js：用户界面框架\n  - Bootstrap：UI组件库\n  - Axios：HTTP客户端",
            "type": "列表项",
            "reason": "前端技术栈的具体内容"
        },
        {
            "content": "- Python Flask：Web框架\n  - FAISS：向量数据库\n  - Sentence Transformers：文本向量化",
            "type": "列表项",
            "reason": "后端技术栈的具体内容"
        },
        {
            "content": "- 大语言模型API：智能分块和问答\n  - 向量相似度搜索：语义匹配\n  - 关键词提取：内容分析",
            "type": "列表项",
            "reason": ""AI服务集成"的具体内容"
        },
        {
            ""content"": "\"部署方案："",
            ""type"": ""子标题"",
            ""reason"": ""小节标题""
        },
        {
            ""content"": "\"一、开发环境\n使用Docker容器化部署，支持快速开发和测试。"",
            ""type"": ""段落"",
            ""reason"": ""开发环境描述""
        },
        {
            ""content"": "\"二、生产环境\n采用微服务架构，支持高并发和水平扩展。"",
            ""type"": ""段落"",
            ""reason"": ""生产环境描述""
        }
    ]
}
```'''
    
    print("测试用例3：复杂的实际AI响应")
    result3 = ai_service._robust_json_parse(test_json3)
    if result3 and 'chunks' in result3:
        print(f"✓ 解析成功，包含 {len(result3['chunks'])} 个块")
        for i, chunk in enumerate(result3['chunks'][:3]):
            content = chunk.get('content', '')[:50] + '...' if len(chunk.get('content', '')) > 50 else chunk.get('content', '')
            print(f"  块 {i+1}: {content}")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例4：极度不规范的JSON
    test_json4 = '''{
        "chunks": [
            {
                "content": "项目技术文档",
                "type": "标题",
                "reason": "文档总标题"
            },
            {
                "content": "第一章：项目背景",
                "type": "章节标题",
                "reason": "章节起始标识"
            },
            {
                content": "技术架构：",
                type": "子标题",
                reason": "小节标题"
            },
            {
                content": "部署方案：",
                "type": "标题",
                "reason": "部署方案标题"
            }
        ]
    }'''
    
    print("测试用例4：极度不规范的JSON")
    result4 = ai_service._robust_json_parse(test_json4)
    if result4 and 'chunks' in result4:
        print(f"✓ 解析成功，包含 {len(result4['chunks'])} 个块")
    else:
        print("✗ 解析失败")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例5：包含特殊字符的JSON
    test_json5 = '''{
        "chunks": [
            {
                "content": "项目技术文档\\n\\n第一章：项目背景",
                "type": "标题",
                "reason": "包含换行符的内容"
            },
            {
                "content": "技术架构：\\n1. 前端技术栈\\n   - React.js：用户界面框架",
                "type": "列表项",
                "reason": "包含转义字符的内容"
            }
        ]
    }'''
    
    print("测试用例5：包含特殊字符的JSON")
    result5 = ai_service._robust_json_parse(test_json5)
    if result5 and 'chunks' in result5:
        print(f"✓ 解析成功，包含 {len(result5['chunks'])} 个块")
    else:
        print("✗ 解析失败")

if __name__ == "__main__":
    test_robust_json_parse() 