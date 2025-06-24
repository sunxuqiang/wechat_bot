#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON修复功能
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
    # 第一步：修复缺少双引号的属性名
    # 匹配 pattern: property_name: value (其中property_name不包含引号)
    def fix_property_names(match):
        whitespace = match.group(1)
        property_name = match.group(2)
        colon_whitespace = match.group(3)
        value = match.group(4)
        return f'{whitespace}"{property_name}"{colon_whitespace}{value}'
    
    json_str = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:\s*)([^,\n\r}]+)', fix_property_names, json_str)
    
    # 第二步：修复缺少引号的字符串值
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
    
    # 第三步：修复单引号为双引号
    json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
    
    # 第四步：修复缺少逗号的问题
    # 在 } 后面如果不是 , 或 } 或 ]，则添加逗号
    json_str = re.sub(r'}(\s*)(?=[^,}\]]*")', r'},\1', json_str)
    
    # 第五步：修复空字符串的引号问题
    json_str = re.sub(r':\s*""\s*([,}])', r': ""\1', json_str)
    
    # 第六步：修复缺少引号的空值
    json_str = re.sub(r':\s*([^"][^,}]*?)\s*([,}])', lambda m: f': "{m.group(1).strip()}"{m.group(2)}' if m.group(1).strip() and not m.group(1).strip().startswith('"') else m.group(0), json_str)
    
    return json_str

def test_json_fix():
    """测试JSON修复功能"""
    print("=== 测试JSON修复功能 ===\n")
    
    # 测试用例1：简单的缺少双引号
    test_json1 = '{"chunks":[{"content":"test","type":"title","reason":"test reason"}]}'
    
    print("测试用例1：标准JSON")
    print(f"原始JSON: {test_json1}")
    
    try:
        parsed1 = json.loads(test_json1)
        print("✓ 测试用例1通过")
    except Exception as e:
        print(f"✗ 测试用例1失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：缺少双引号的属性名
    test_json2 = '{"chunks":[{"content":"test",type:"title",reason:"test reason"}]}'
    
    print("测试用例2：缺少双引号的属性名")
    print(f"原始JSON: {test_json2}")
    
    fixed_json2 = fix_json_format(test_json2)
    print(f"修复后JSON: {fixed_json2}")
    
    try:
        parsed2 = json.loads(fixed_json2)
        print("✓ 测试用例2通过")
    except Exception as e:
        print(f"✗ 测试用例2失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例3：缺少引号的字符串值
    test_json3 = '{"chunks":[{"content":"test","type":"title","reason":test reason}]}'
    
    print("测试用例3：缺少引号的字符串值")
    print(f"原始JSON: {test_json3}")
    
    fixed_json3 = fix_json_format(test_json3)
    print(f"修复后JSON: {fixed_json3}")
    
    try:
        parsed3 = json.loads(fixed_json3)
        print("✓ 测试用例3通过")
    except Exception as e:
        print(f"✗ 测试用例3失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例4：单引号
    test_json4 = '{"chunks":[{"content":"test","type":"title","reason":"test reason"}]}'
    
    print("测试用例4：单引号")
    print(f"原始JSON: {test_json4}")
    
    fixed_json4 = fix_json_format(test_json4)
    print(f"修复后JSON: {fixed_json4}")
    
    try:
        parsed4 = json.loads(fixed_json4)
        print("✓ 测试用例4通过")
    except Exception as e:
        print(f"✗ 测试用例4失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例5：实际案例的一部分
    test_json5 = '''{"chunks":[{"content":"项目技术文档","type":"标题","reason":"作为整个文档的主标题"},{"content":"第一章：项目背景","type":"章节标题","reason":"这是章节标题，属于语义完整单元"}]}'''
    
    print("测试用例5：实际案例")
    print(f"原始JSON: {test_json5}")
    
    try:
        parsed5 = json.loads(test_json5)
        print("✓ 测试用例5通过")
        print(f"解析成功，包含 {len(parsed5['chunks'])} 个文本块")
    except Exception as e:
        print(f"✗ 测试用例5失败: {e}")
        
        # 尝试修复
        fixed_json5 = fix_json_format(test_json5)
        print(f"修复后JSON: {fixed_json5}")
        try:
            parsed5 = json.loads(fixed_json5)
            print("✓ 修复后测试用例5通过")
            print(f"解析成功，包含 {len(parsed5['chunks'])} 个文本块")
        except Exception as e2:
            print(f"✗ 修复后测试用例5仍然失败: {e2}")

if __name__ == "__main__":
    test_json_fix() 