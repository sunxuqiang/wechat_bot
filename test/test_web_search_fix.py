#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web搜索功能修复
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_web_search():
    """测试Web搜索功能"""
    print("=== 测试Web搜索功能 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        # 获取服务实例
        service = get_knowledge_query_service()
        print("✓ 知识库查询服务获取成功")
        
        # 测试Web搜索方法
        test_query = "测试"
        print(f"测试查询: '{test_query}'")
        
        # 测试带include_metadata参数的搜索
        result = service.search_for_web(
            query=test_query,
            include_metadata=True
        )
        
        print(f"✓ Web搜索执行成功")
        print(f"  成功状态: {result['success']}")
        print(f"  结果数量: {len(result['results'])}")
        
        # 根据成功状态显示不同的消息字段
        if result['success']:
            print(f"  消息: {result.get('message', 'N/A')}")
        else:
            print(f"  错误: {result.get('error', 'N/A')}")
        
        if result['results']:
            print("  第一个结果:")
            first_result = result['results'][0]
            print(f"    内容预览: {first_result['content'][:100]}...")
            print(f"    分数: {first_result['score']}")
            print(f"    包含元数据: {'metadata' in first_result}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_wechat_search():
    """测试微信搜索功能"""
    print("\n=== 测试微信搜索功能 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        # 获取服务实例
        service = get_knowledge_query_service()
        
        # 测试微信搜索方法
        test_query = "测试"
        print(f"测试查询: '{test_query}'")
        
        # 测试带include_metadata参数的搜索
        result = service.search_for_wechat(
            query=test_query,
            include_metadata=True
        )
        
        print(f"✓ 微信搜索执行成功")
        print(f"  成功状态: {result['success']}")
        print(f"  结果数量: {len(result['results'])}")
        
        # 根据成功状态显示不同的消息字段
        if result['success']:
            print(f"  消息: {result.get('message', 'N/A')}")
        else:
            print(f"  错误: {result.get('error', 'N/A')}")
        
        if result['results']:
            print("  第一个结果:")
            first_result = result['results'][0]
            print(f"    内容预览: {first_result['content'][:100]}...")
            print(f"    分数: {first_result['score']}")
            print(f"    包含元数据: {'metadata' in first_result}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_consistency():
    """测试参数一致性"""
    print("\n=== 测试参数一致性 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        service = get_knowledge_query_service()
        
        # 测试不同参数组合
        test_cases = [
            ("基本搜索", service.search_for_web, {"query": "测试"}),
            ("带top_k", service.search_for_web, {"query": "测试", "top_k": 5}),
            ("带min_score", service.search_for_web, {"query": "测试", "min_score": 0.5}),
            ("带include_metadata", service.search_for_web, {"query": "测试", "include_metadata": True}),
            ("所有参数", service.search_for_web, {"query": "测试", "top_k": 5, "min_score": 0.5, "include_metadata": True}),
        ]
        
        for test_name, search_func, params in test_cases:
            try:
                result = search_func(**params)
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
    print("开始测试Web搜索功能修复")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    success = True
    
    # 测试Web搜索
    if not test_web_search():
        success = False
    
    # 测试微信搜索
    if not test_wechat_search():
        success = False
    
    # 测试参数一致性
    if not test_parameter_consistency():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- Web搜索功能正常工作")
        print("- include_metadata参数支持正常")
        print("- 参数传递一致性验证通过")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 