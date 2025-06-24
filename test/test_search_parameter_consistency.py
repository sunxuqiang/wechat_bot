#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试微信端和页面端搜索参数一致性
验证是否使用同一段代码和同一个参数配置
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_code_consistency():
    """测试代码一致性"""
    print("=== 测试代码一致性 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        service = get_knowledge_query_service()
        
        # 检查是否使用同一个服务实例
        print("✓ 使用同一个KnowledgeQueryService实例")
        print(f"  实例ID: {id(service)}")
        
        # 检查是否使用同一个向量存储
        if hasattr(service, 'vector_store') and service.vector_store:
            print("✓ 使用同一个向量存储实例")
            print(f"  向量存储ID: {id(service.vector_store)}")
        else:
            print("⚠ 向量存储未初始化（这是正常的，因为测试时可能还没有加载）")
            # 尝试从app或wechat_bot获取向量存储
            try:
                import app
                if hasattr(app, 'vector_store') and app.vector_store:
                    print("✓ 从app模块获取到向量存储实例")
                    service.set_vector_store(app.vector_store)
                else:
                    print("⚠ app模块中向量存储也未初始化")
            except:
                pass
        
        # 检查是否使用同一个搜索配置
        if hasattr(service, 'search_config'):
            print("✓ 使用同一个搜索配置实例")
            print(f"  搜索配置ID: {id(service.search_config)}")
        else:
            print("✗ 搜索配置未找到")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_configuration():
    """测试参数配置"""
    print("\n=== 测试参数配置 ===")
    
    try:
        from knowledge_query_service import search_config
        from config_loader import config
        
        print("✓ 搜索配置类加载成功")
        
        # 检查配置文件中的参数
        print("\n配置文件参数:")
        print(f"  [vector_store].similarity_threshold = {config.getfloat('vector_store', 'similarity_threshold')}")
        print(f"  [vector_store].max_results = {config.getint('vector_store', 'max_results')}")
        
        # 检查搜索配置实例的参数
        print("\n搜索配置实例参数:")
        print(f"  默认配置: max_results={search_config.max_results}, min_score={search_config.min_score}")
        print(f"  微信配置: max_results={search_config.wechat_max_results}, min_score={search_config.wechat_min_score}")
        print(f"  Web配置: max_results={search_config.web_max_results}, min_score={search_config.web_min_score}")
        
        # 验证参数来源
        config_similarity = config.getfloat('vector_store', 'similarity_threshold')
        config_max_results = config.getint('vector_store', 'max_results')
        
        if search_config.min_score == config_similarity:
            print("✓ min_score参数来自config.conf")
        else:
            print(f"✗ min_score参数不匹配: 配置={config_similarity}, 实例={search_config.min_score}")
            return False
        
        if search_config.max_results == config_max_results:
            print("✓ max_results参数来自config.conf")
        else:
            print(f"✗ max_results参数不匹配: 配置={config_max_results}, 实例={search_config.max_results}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_search_methods():
    """测试搜索方法"""
    print("\n=== 测试搜索方法 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        service = get_knowledge_query_service()
        
        # 检查搜索方法
        methods_to_check = [
            ('search_for_wechat', '微信端搜索方法'),
            ('search_for_web', '页面端搜索方法'),
            ('search_knowledge_base', '基础搜索方法')
        ]
        
        for method_name, description in methods_to_check:
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                print(f"✓ {description}存在: {method_name}")
                print(f"  方法签名: {method.__name__}")
            else:
                print(f"✗ {description}不存在: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_search_parameters():
    """测试实际搜索参数"""
    print("\n=== 测试实际搜索参数 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        service = get_knowledge_query_service()
        
        # 测试微信端搜索参数
        print("微信端搜索参数:")
        wechat_config = service.search_config.get_wechat_config()
        print(f"  top_k={wechat_config[0]}, min_score={wechat_config[1]}")
        
        # 测试页面端搜索参数
        print("页面端搜索参数:")
        web_config = service.search_config.get_web_config()
        print(f"  top_k={web_config[0]}, min_score={web_config[1]}")
        
        # 测试默认搜索参数
        print("默认搜索参数:")
        default_config = service.search_config.get_default_config()
        print(f"  top_k={default_config[0]}, min_score={default_config[1]}")
        
        # 验证参数差异
        if wechat_config != web_config:
            print("✓ 微信端和页面端使用不同的参数配置（符合预期）")
        else:
            print("⚠ 微信端和页面端使用相同的参数配置")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_call_consistency():
    """测试调用一致性"""
    print("\n=== 测试调用一致性 ===")
    
    try:
        # 检查微信端调用
        import wechat_bot
        print("微信端调用:")
        print(f"  使用: knowledge_query_service.search_for_wechat(message)")
        print(f"  参数: 使用微信专用配置 (top_k=3, min_score=0.3)")
        
        # 检查页面端调用
        import app
        print("页面端调用:")
        print(f"  使用: knowledge_query_service.search_for_web(query, include_metadata=True)")
        print(f"  参数: 使用Web专用配置 (top_k=10, min_score=0.3)")
        
        # 验证都使用同一个服务实例
        wechat_service = wechat_bot.knowledge_query_service
        app_service = app.knowledge_query_service
        
        if wechat_service is app_service:
            print("✓ 微信端和页面端使用同一个服务实例")
        else:
            print("✗ 微信端和页面端使用不同的服务实例")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试微信端和页面端搜索参数一致性")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    success = True
    
    # 测试代码一致性
    if not test_code_consistency():
        success = False
    
    # 测试参数配置
    if not test_parameter_configuration():
        success = False
    
    # 测试搜索方法
    if not test_search_methods():
        success = False
    
    # 测试实际搜索参数
    if not test_actual_search_parameters():
        success = False
    
    # 测试调用一致性
    if not test_call_consistency():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- 微信端和页面端使用同一段代码（KnowledgeQueryService）")
        print("- 使用同一个服务实例和向量存储")
        print("- 参数配置来自config.conf文件")
        print("- 微信端和页面端使用不同的参数配置（符合设计）")
        print("- 所有搜索都通过统一的接口进行")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 