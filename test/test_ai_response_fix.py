#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI响应JSON修复功能
"""

import json
import re

def fix_json_format(json_str: str) -> str:
    """
    修复不标准的JSON格式
    
    Args:
        json_str: 原始JSON字符串
        
    Returns:
        str: 修复后的JSON字符串
    """
    # 第一步：清理特殊字符和转义字符
    # 移除零宽字符
    json_str = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F]', '', json_str)
    
    # 修复转义的双引号
    json_str = re.sub(r'\\"', '"', json_str)
    
    # 修复转义的反斜杠
    json_str = re.sub(r'\\\\', '\\', json_str)
    
    # 第二步：修复单引号为双引号
    json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
    
    # 第三步：修复缺少双引号的属性名
    # 匹配 pattern: property_name: value (其中property_name不包含引号)
    def fix_property_names(match):
        whitespace = match.group(1)
        property_name = match.group(2)
        colon_whitespace = match.group(3)
        value = match.group(4)
        return f'{whitespace}"{property_name}"{colon_whitespace}{value}'
    
    # 更精确的匹配，避免匹配数组中的内容
    json_str = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:\s*)([^,\n\r}]+?)(\s*[,}])', 
                     lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}{m.group(4)}{m.group(5)}', json_str)
    
    # 第四步：修复缺少引号的字符串值
    # 匹配 pattern: "property": value (其中value不是数字、true、false、null、数组、对象)
    def fix_string_values(match):
        property_part = match.group(1)  # "property":
        value_part = match.group(2).strip()  # value
        
        # 如果值不是数字、布尔值、null、数组、对象，且不是以引号开头，则添加引号
        if (not value_part.startswith('"') and 
            not value_part.startswith("'") and
            not value_part.isdigit() and
            not value_part.lower() in ['true', 'false', 'null'] and
            not value_part.startswith('[') and
            not value_part.startswith('{') and
            not value_part.endswith(']') and
            not value_part.endswith('}')):
            return f'{property_part} "{value_part}"'
        return match.group(0)
    
    json_str = re.sub(r'("[\w]+"\s*:\s*)([^,\n\r}]+)', fix_string_values, json_str)
    
    # 第五步：修复多余的引号
    json_str = re.sub(r'""([^"]*?)""', r'"\1"', json_str)
    
    # 第六步：修复缺少逗号的问题
    json_str = re.sub(r'}(\s*)(?=[^,}\]]*")', r'},\1', json_str)
    
    return json_str

def test_ai_response_fix():
    """测试AI响应JSON修复功能"""
    print("=== 测试AI响应JSON修复功能 ===\n")
    
    # 测试用例1：实际的AI响应格式（从日志中提取）
    test_json1 = '''```json
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
    
    print("测试用例1：实际的AI响应格式")
    print("原始JSON长度:", len(test_json1))
    
    # 清理markdown代码块
    cleaned_json = test_json1.strip()
    if cleaned_json.startswith('```json'):
        cleaned_json = cleaned_json[7:]
    elif cleaned_json.startswith('```'):
        cleaned_json = cleaned_json[3:]
    
    if cleaned_json.endswith('```'):
        cleaned_json = cleaned_json[:-3]
    
    cleaned_json = cleaned_json.strip()
    
    print("清理后JSON长度:", len(cleaned_json))
    
    # 尝试修复JSON
    fixed_json = fix_json_format(cleaned_json)
    print("修复后JSON长度:", len(fixed_json))
    
    try:
        parsed = json.loads(fixed_json)
        print("✓ 测试用例1通过")
        print(f"解析成功，包含 {len(parsed['chunks'])} 个文本块")
        
        # 显示前几个块的内容
        for i, chunk in enumerate(parsed['chunks'][:3]):
            print(f"  块 {i+1}: {chunk.get('content', '')[:50]}...")
            
    except Exception as e:
        print(f"✗ 测试用例1失败: {e}")
        print(f"错误位置: {e.pos if hasattr(e, 'pos') else '未知'}")
        
        # 显示修复后的JSON的前200个字符
        print("修复后JSON前200字符:")
        print(fixed_json[:200])
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：另一个实际的AI响应格式
    test_json2 = '''```json
{
    "chunks": [
        {
            "content": "项目技术文档",
            "type": "标题",
            "reason": "作为整个文档的总标题"
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
    
    print("测试用例2：另一个实际的AI响应格式")
    print("原始JSON长度:", len(test_json2))
    
    # 清理markdown代码块
    cleaned_json2 = test_json2.strip()
    if cleaned_json2.startswith('```json'):
        cleaned_json2 = cleaned_json2[7:]
    elif cleaned_json2.startswith('```'):
        cleaned_json2 = cleaned_json2[3:]
    
    if cleaned_json2.endswith('```'):
        cleaned_json2 = cleaned_json2[:-3]
    
    cleaned_json2 = cleaned_json2.strip()
    
    print("清理后JSON长度:", len(cleaned_json2))
    
    # 尝试修复JSON
    fixed_json2 = fix_json_format(cleaned_json2)
    print("修复后JSON长度:", len(fixed_json2))
    
    try:
        parsed2 = json.loads(fixed_json2)
        print("✓ 测试用例2通过")
        print(f"解析成功，包含 {len(parsed2['chunks'])} 个文本块")
        
        # 显示前几个块的内容
        for i, chunk in enumerate(parsed2['chunks'][:3]):
            print(f"  块 {i+1}: {chunk.get('content', '')[:50]}...")
            
    except Exception as e:
        print(f"✗ 测试用例2失败: {e}")
        print(f"错误位置: {e.pos if hasattr(e, 'pos') else '未知'}")
        
        # 显示修复后的JSON的前200个字符
        print("修复后JSON前200字符:")
        print(fixed_json2[:200])

if __name__ == "__main__":
    test_ai_response_fix() 