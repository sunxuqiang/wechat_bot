#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试文本内容
"""

def debug_text_content():
    """调试传递给AI分块服务的文本内容"""
    print("=== 调试文本内容 ===\n")
    
    # 模拟从文件读取的文本
    test_text = """
智能系统使用手册

第一章：系统概述
本智能系统是一款基于人工智能技术的知识管理平台，旨在帮助用户高效地管理和查询文档信息。

系统特点：
1. 智能文档处理
   支持多种文档格式，包括PDF、Word、Excel、TXT等。
   自动提取文档内容，生成结构化数据。

2. 高效搜索功能
   基于向量数据库的语义搜索。
   支持关键词匹配和相似度排序。

3. 用户友好界面
   简洁直观的操作界面。
   支持批量操作和实时预览。
    """
    
    print("1. 原始文本:")
    print(f"   长度: {len(test_text)} 字符")
    print(f"   内容: {repr(test_text)}")
    
    # 检查是否包含特殊字符
    print(f"\n2. 检查特殊字符:")
    problem_string = '\n    "chunks"'
    if problem_string in test_text:
        print("   ✗ 包含问题字符串: '\\n    \"chunks\"'")
        print(f"   位置: {test_text.find(problem_string)}")
    else:
        print("   ✓ 不包含问题字符串")
    
    # 检查其他可能的格式化字符
    format_chars = ['{', '}', '\\n', '\\t']
    for char in format_chars:
        if char in test_text:
            print(f"   包含字符: {repr(char)}")
    
    # 尝试格式化
    print(f"\n3. 尝试格式化:")
    try:
        prompt_template = "测试文本：{text}"
        result = prompt_template.format(text=test_text)
        print("   ✓ 格式化成功")
    except Exception as e:
        print(f"   ✗ 格式化失败: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
    
    # 清理文本
    print(f"\n4. 清理文本:")
    cleaned_text = test_text.strip()
    print(f"   清理后长度: {len(cleaned_text)} 字符")
    print(f"   清理后内容: {repr(cleaned_text)}")
    
    # 再次尝试格式化
    try:
        result = prompt_template.format(text=cleaned_text)
        print("   ✓ 清理后格式化成功")
    except Exception as e:
        print(f"   ✗ 清理后格式化失败: {str(e)}")

if __name__ == "__main__":
    debug_text_content() 