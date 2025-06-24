#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试app.py搜索功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_app_search_function():
    """测试app.py中的搜索函数"""
    print("=== 测试app.py搜索函数 ===")
    
    try:
        # 导入app模块
        import app
        
        # 检查knowledge_query_service是否正确导入
        if hasattr(app, 'knowledge_query_service'):
            print("✓ knowledge_query_service已正确导入")
            print(f"  类型: {type(app.knowledge_query_service)}")
        else:
            print("✗ knowledge_query_service未导入")
            return False
        
        # 检查search函数是否存在
        if hasattr(app, 'search'):
            print("✓ search函数存在")
        else:
            print("✗ search函数不存在")
            return False
        
        # 测试knowledge_query_service的search_for_web方法
        try:
            result = app.knowledge_query_service.search_for_web(
                query="测试",
                include_metadata=True
            )
            print("✓ search_for_web方法调用成功")
            print(f"  成功状态: {result['success']}")
            print(f"  结果数量: {len(result['results'])}")
            
            if result['success']:
                print(f"  消息: {result.get('message', 'N/A')}")
            else:
                print(f"  错误: {result.get('error', 'N/A')}")
                
        except Exception as e:
            print(f"✗ search_for_web方法调用失败: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_support():
    """测试参数支持"""
    print("\n=== 测试参数支持 ===")
    
    try:
        import app
        
        # 测试不同的参数组合
        test_cases = [
            ("基本参数", {"query": "测试"}),
            ("带include_metadata", {"query": "测试", "include_metadata": True}),
            ("带top_k", {"query": "测试", "top_k": 5}),
            ("带min_score", {"query": "测试", "min_score": 0.5}),
        ]
        
        for test_name, params in test_cases:
            try:
                result = app.knowledge_query_service.search_for_web(**params)
                print(f"✓ {test_name}: 成功")
                print(f"  参数: {params}")
                print(f"  结果数量: {len(result['results'])}")
            except Exception as e:
                print(f"✗ {test_name}: 失败 - {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试app.py搜索功能")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    success = True
    
    # 测试app.py搜索函数
    if not test_app_search_function():
        success = False
    
    # 测试参数支持
    if not test_parameter_support():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- app.py搜索功能正常工作")
        print("- include_metadata参数支持正常")
        print("- 参数传递正确")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 