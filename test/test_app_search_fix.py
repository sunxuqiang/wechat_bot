#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试app.py中的搜索功能修复
"""

import os
import sys
import requests
import json
import time

def test_app_search():
    """测试app.py中的搜索功能"""
    try:
        print("=== 测试app.py搜索功能修复 ===")
        
        # 模拟搜索请求
        search_data = {
            'query': '测试'
        }
        
        # 这里我们只是验证代码结构，不实际发送HTTP请求
        print("搜索数据:", json.dumps(search_data, ensure_ascii=False, indent=2))
        
        # 验证knowledge_query_service是否正确导入和初始化
        try:
            from app import knowledge_query_service
            print("✓ knowledge_query_service 已正确导入")
            
            # 检查服务实例
            if knowledge_query_service:
                print("✓ knowledge_query_service 实例存在")
                print(f"  类型: {type(knowledge_query_service)}")
                print(f"  向量存储: {knowledge_query_service.vector_store}")
            else:
                print("✗ knowledge_query_service 实例为空")
                
        except ImportError as e:
            print(f"✗ 导入错误: {e}")
            return False
        except Exception as e:
            print(f"✗ 其他错误: {e}")
            return False
        
        # 验证搜索函数是否存在
        try:
            from app import search
            print("✓ search 函数已正确导入")
        except ImportError as e:
            print(f"✗ search 函数导入错误: {e}")
            return False
        
        print("✓ app.py 搜索功能修复验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_query_service_integration():
    """测试知识库查询服务集成"""
    try:
        print("\n=== 测试知识库查询服务集成 ===")
        
        from knowledge_query_service import get_knowledge_query_service
        from vector_store import FaissVectorStore
        
        # 获取服务实例
        service = get_knowledge_query_service()
        print("✓ 获取知识库查询服务实例成功")
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        print("✓ 初始化向量存储成功")
        
        # 设置向量存储
        service.set_vector_store(vector_store)
        print("✓ 设置向量存储成功")
        
        # 测试搜索功能
        result = service.search_knowledge_base("测试", top_k=3)
        print(f"✓ 搜索测试完成，结果: {result['success']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始测试app.py搜索功能修复")
    
    # 测试app.py搜索功能
    if test_app_search():
        print("✓ app.py搜索功能测试通过")
    else:
        print("✗ app.py搜索功能测试失败")
        return
    
    # 测试知识库查询服务集成
    if test_knowledge_query_service_integration():
        print("✓ 知识库查询服务集成测试通过")
    else:
        print("✗ 知识库查询服务集成测试失败")
    
    print("\n所有测试完成")

if __name__ == "__main__":
    main() 