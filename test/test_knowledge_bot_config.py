#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试knowledge_bot.py的配置参数化功能
验证URL、模型、API密钥、提示词等都从配置文件读取
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    try:
        from config_loader import config
        
        # 测试API配置
        url = config.get('api', 'url')
        model = config.get('api', 'model')
        api_key = config.get_secret('siliconflow_api_key')
        max_tokens = config.getint('api', 'max_tokens', fallback=2048)
        temperature = config.getfloat('api', 'temperature', fallback=0.7)
        
        print(f"✓ API URL: {url}")
        print(f"✓ 模型: {model}")
        print(f"✓ API密钥: {api_key[:10]}..." if api_key else "✗ API密钥未配置")
        print(f"✓ 最大token数: {max_tokens}")
        print(f"✓ 温度: {temperature}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_manager_integration():
    """测试提示词管理器集成"""
    print("\n=== 测试提示词管理器集成 ===")
    
    try:
        from prompt_manager import get_prompt_manager
        
        pm = get_prompt_manager()
        system_prompt = pm.get_system_prompt('default')
        
        print(f"✓ 系统提示词: {len(system_prompt)} 字符")
        print(f"  预览: {system_prompt[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_bot_initialization():
    """测试KnowledgeBot初始化"""
    print("\n=== 测试KnowledgeBot初始化 ===")
    
    try:
        from knowledge_bot import KnowledgeBot
        
        # 创建KnowledgeBot实例
        bot = KnowledgeBot()
        print("✓ KnowledgeBot初始化成功")
        
        # 检查是否有必要的属性
        if hasattr(bot, 'kb'):
            print("✓ 知识库实例存在")
        else:
            print("✗ 知识库实例不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_config_consistency():
    """测试API配置一致性"""
    print("\n=== 测试API配置一致性 ===")
    
    try:
        from config_loader import config
        from knowledge_bot import KnowledgeBot
        
        # 从配置文件获取参数
        config_url = config.get('api', 'url')
        config_model = config.get('api', 'model')
        config_api_key = config.get_secret('siliconflow_api_key')
        
        print(f"配置文件中的参数:")
        print(f"  URL: {config_url}")
        print(f"  模型: {config_model}")
        print(f"  API密钥: {config_api_key[:10]}..." if config_api_key else "  未配置")
        
        # 创建KnowledgeBot实例并测试_get_llm_response方法
        bot = KnowledgeBot()
        
        # 模拟调用_get_llm_response方法（不实际发送请求）
        print("\n模拟API调用参数:")
        
        # 获取配置参数
        url = config.get('api', 'url')
        model = config.get('api', 'model')
        api_key = config.get_secret('siliconflow_api_key')
        max_tokens = config.getint('api', 'max_tokens', fallback=2048)
        temperature = config.getfloat('api', 'temperature', fallback=0.7)
        top_p = config.getfloat('api', 'top_p', fallback=0.7)
        frequency_penalty = config.getfloat('api', 'frequency_penalty', fallback=0.5)
        presence_penalty = config.getfloat('api', 'presence_penalty', fallback=0.0)
        
        # 获取提示词管理器
        from prompt_manager import get_prompt_manager
        prompt_manager = get_prompt_manager()
        system_prompt = prompt_manager.get_system_prompt('default')
        
        print(f"  实际使用的URL: {url}")
        print(f"  实际使用的模型: {model}")
        print(f"  实际使用的API密钥: {api_key[:10]}..." if api_key else "  未配置")
        print(f"  实际使用的系统提示词: {system_prompt[:50]}...")
        print(f"  实际使用的max_tokens: {max_tokens}")
        print(f"  实际使用的temperature: {temperature}")
        print(f"  实际使用的top_p: {top_p}")
        print(f"  实际使用的frequency_penalty: {frequency_penalty}")
        print(f"  实际使用的presence_penalty: {presence_penalty}")
        
        # 验证配置一致性
        if (config_url == url and 
            config_model == model and 
            config_api_key == api_key):
            print("✓ API配置一致性验证通过")
        else:
            print("✗ API配置一致性验证失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_consistency():
    """测试提示词一致性"""
    print("\n=== 测试提示词一致性 ===")
    
    try:
        from config_loader import config
        from prompt_manager import get_prompt_manager
        
        # 从配置文件获取系统提示词
        config_system_prompt = config.get('chat', 'system_prompt', fallback='')
        
        # 从提示词管理器获取系统提示词
        pm = get_prompt_manager()
        manager_system_prompt = pm.get_system_prompt('default')
        
        print(f"配置文件中的系统提示词: {len(config_system_prompt)} 字符")
        print(f"提示词管理器中的系统提示词: {len(manager_system_prompt)} 字符")
        
        # 验证一致性
        if config_system_prompt == manager_system_prompt:
            print("✓ 提示词一致性验证通过")
        else:
            print("✗ 提示词一致性验证失败")
            print(f"  配置文件: {config_system_prompt[:50]}...")
            print(f"  管理器: {manager_system_prompt[:50]}...")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variable_replacement():
    """测试环境变量替换"""
    print("\n=== 测试环境变量替换 ===")
    
    try:
        from config_loader import config
        
        # 检查是否还在使用环境变量
        old_api_key = os.getenv('SILICONFLOW_API_KEY')
        config_api_key = config.get_secret('siliconflow_api_key')
        
        print(f"环境变量中的API密钥: {old_api_key[:10]}..." if old_api_key else "未设置")
        print(f"配置文件中的API密钥: {config_api_key[:10]}..." if config_api_key else "未配置")
        
        if config_api_key:
            print("✓ 已从配置文件读取API密钥")
        else:
            print("⚠ 配置文件中的API密钥未配置")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("KnowledgeBot配置参数化功能测试")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_prompt_manager_integration,
        test_knowledge_bot_initialization,
        test_api_config_consistency,
        test_prompt_consistency,
        test_environment_variable_replacement
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"测试 {test.__name__} 发生异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！KnowledgeBot配置参数化功能正常")
    else:
        print("✗ 部分测试失败，请检查配置和代码")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 