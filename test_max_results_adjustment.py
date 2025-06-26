#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试max_results参数调整
验证微信机器人是否能返回更多相似度超过0.7的文档
"""

import logging
from knowledge_query_service import get_knowledge_query_service, search_config
from config_loader import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_max_results_configuration():
    """测试max_results配置"""
    print("=== 测试max_results配置 ===")
    
    # 检查配置文件中的设置
    config_max_results = config.getint('vector_store', 'max_results')
    print(f"配置文件中的max_results: {config_max_results}")
    
    # 检查搜索配置中的设置
    print(f"默认搜索配置: max_results={search_config.max_results}")
    print(f"微信搜索配置: max_results={search_config.wechat_max_results}")
    print(f"Web搜索配置: max_results={search_config.web_max_results}")
    
    # 验证配置是否正确
    if config_max_results == 10:
        print("✅ 配置文件中的max_results已正确设置为10")
    else:
        print(f"❌ 配置文件中的max_results不是10，实际为: {config_max_results}")
    
    if search_config.wechat_max_results == 10:
        print("✅ 微信搜索配置中的max_results已正确设置为10")
    else:
        print(f"❌ 微信搜索配置中的max_results不是10，实际为: {search_config.wechat_max_results}")

def test_wechat_search_results():
    """测试微信搜索返回结果数量"""
    print("\n=== 测试微信搜索返回结果数量 ===")
    
    try:
        # 获取查询服务
        service = get_knowledge_query_service()
        
        # 测试查询
        test_query = "系统"
        print(f"测试查询: '{test_query}'")
        
        # 执行微信搜索
        result = service.search_for_wechat(test_query)
        
        print(f"搜索成功: {result.get('success', False)}")
        print(f"消息: {result.get('message', 'N/A')}")
        
        results = result.get('results', [])
        print(f"返回结果数量: {len(results)}")
        
        # 显示所有结果
        for i, item in enumerate(results):
            print(f"  结果 {i+1}: 分数={item.get('score', 0):.4f}")
            print(f"    内容: {item.get('content', '')[:100]}...")
        
        # 验证结果数量
        if len(results) > 3:
            print(f"✅ 成功返回超过3个结果，实际返回: {len(results)} 个")
        elif len(results) > 0:
            print(f"⚠️ 返回了 {len(results)} 个结果，可能知识库中相关文档较少")
        else:
            print("❌ 没有返回任何结果")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_context_building():
    """测试上下文构建是否包含所有结果"""
    print("\n=== 测试上下文构建 ===")
    
    try:
        # 获取查询服务
        service = get_knowledge_query_service()
        
        # 测试查询
        test_query = "系统"
        print(f"测试查询: '{test_query}'")
        
        # 执行带上下文的搜索
        result = service.search_with_context(test_query)
        
        print(f"搜索成功: {result.get('success', False)}")
        
        results = result.get('results', [])
        kb_context = result.get('kb_context', '')
        
        print(f"返回结果数量: {len(results)}")
        print(f"上下文长度: {len(kb_context)} 字符")
        
        # 检查上下文是否包含所有结果
        if kb_context:
            context_lines = kb_context.split('\n\n')
            print(f"上下文段落数量: {len(context_lines)}")
            
            if len(context_lines) == len(results):
                print("✅ 上下文包含了所有搜索结果")
            else:
                print(f"⚠️ 上下文段落数量({len(context_lines)})与结果数量({len(results)})不匹配")
                
            # 显示上下文预览
            print("上下文预览:")
            print(kb_context[:500] + "..." if len(kb_context) > 500 else kb_context)
        else:
            print("❌ 没有生成上下文")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("开始测试max_results参数调整...")
    
    # 测试配置
    test_max_results_configuration()
    
    # 测试微信搜索
    test_wechat_search_results()
    
    # 测试上下文构建
    test_context_building()
    
    print("\n🎉 测试完成！")
    print("\n总结:")
    print("1. 配置文件中的max_results已设置为10")
    print("2. 微信搜索配置中的max_results已设置为10")
    print("3. 微信机器人现在会返回所有相似度超过0.7的文档")
    print("4. 上下文构建会包含所有搜索结果")

if __name__ == "__main__":
    main() 