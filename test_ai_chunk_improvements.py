#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI分块服务改进
"""

import logging
from ai_chunk_service import AIChunkService

logging.basicConfig(level=logging.INFO)

def test_json_fix():
    """测试JSON修复功能"""
    print("=== 测试JSON修复功能 ===")
    
    service = AIChunkService()
    
    # 测试截断的JSON
    truncated_json = '{"chunks": [{"content": "test", "type": "test"'
    fixed = service._fix_truncated_json(truncated_json)
    print(f"修复前: {truncated_json}")
    print(f"修复后: {fixed}")
    
    # 测试解析
    result = service._robust_json_parse(fixed)
    print(f"解析结果: {result is not None}")
    
    print("✅ JSON修复测试完成")

def test_ssl_session():
    """测试SSL session"""
    print("\n=== 测试SSL session ===")
    
    service = AIChunkService()
    
    try:
        session = service._create_session()
        print(f"SSL session创建成功: {session is not None}")
        print(f"SSL验证: {session.verify}")
        print("✅ SSL session测试完成")
    except Exception as e:
        print(f"❌ SSL session测试失败: {e}")

def main():
    """主测试函数"""
    print("开始测试AI分块服务改进...")
    
    test_json_fix()
    test_ssl_session()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main() 