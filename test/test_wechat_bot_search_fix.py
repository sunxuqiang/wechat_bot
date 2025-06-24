#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 wechat_bot.py 中知识库查询服务集成的修复
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_wechat_bot_integration():
    """测试wechat_bot.py中知识库查询服务的集成"""
    print("=== 测试wechat_bot.py知识库查询服务集成 ===")
    
    try:
        # 测试导入
        print("测试导入wechat_bot模块...")
        import wechat_bot
        print("✓ wechat_bot模块导入成功")
        
        # 检查knowledge_query_service是否已导入
        if hasattr(wechat_bot, 'knowledge_query_service'):
            print("✓ knowledge_query_service已正确导入")
            print(f"  类型: {type(wechat_bot.knowledge_query_service)}")
        else:
            print("✗ knowledge_query_service未找到")
            return False
        
        # 检查向量存储是否已设置
        if hasattr(wechat_bot.knowledge_query_service, 'vector_store'):
            vector_store = wechat_bot.knowledge_query_service.vector_store
            if vector_store is not None:
                print("✓ 向量存储已正确设置")
                print(f"  向量存储类型: {type(vector_store)}")
            else:
                print("✗ 向量存储未设置")
                return False
        else:
            print("✗ knowledge_query_service没有vector_store属性")
            return False
        
        # 测试搜索功能
        print("测试搜索功能...")
        search_results = wechat_bot.knowledge_query_service.search("测试", top_k=3, min_score=0.3)
        if search_results is not None:
            print("✓ 搜索功能正常")
            print(f"  搜索结果数量: {len(search_results)}")
        else:
            print("✗ 搜索功能异常")
            return False
        
        print("✓ wechat_bot.py知识库查询服务集成测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_wechat_bot_search_function():
    """测试wechat_bot.py中的搜索函数"""
    print("\n=== 测试wechat_bot.py搜索函数 ===")
    
    try:
        import wechat_bot
        
        # 检查search_knowledge_base函数是否存在
        if hasattr(wechat_bot, 'search_knowledge_base'):
            print("✓ search_knowledge_base函数存在")
            
            # 测试函数调用
            results = wechat_bot.search_knowledge_base("测试查询")
            if results is not None:
                print("✓ search_knowledge_base函数调用成功")
                print(f"  返回结果类型: {type(results)}")
            else:
                print("✗ search_knowledge_base函数返回None")
                return False
        else:
            print("✗ search_knowledge_base函数不存在")
            return False
        
        print("✓ wechat_bot.py搜索函数测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试wechat_bot.py知识库查询服务集成修复")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    success = True
    
    # 测试集成
    if not test_wechat_bot_integration():
        success = False
    
    # 测试搜索函数
    if not test_wechat_bot_search_function():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 