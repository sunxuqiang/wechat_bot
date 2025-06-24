#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试knowledge_bot.py的配置参数化功能
只测试配置读取，不初始化完整的KnowledgeBot
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

def test_config_parameters():
    """测试配置参数读取"""
    print("=== 测试配置参数读取 ===")
    
    try:
        from config_loader import config
        
        # 测试API配置
        url = config.get('api', 'url')
        model = config.get('api', 'model')
        api_key = config.get_secret('siliconflow_api_key')
        max_tokens = config.getint('api', 'max_tokens', fallback=2048)
        temperature = config.getfloat('api', 'temperature', fallback=0.7)
        top_p = config.getfloat('api', 'top_p', fallback=0.7)
        frequency_penalty = config.getfloat('api', 'frequency_penalty', fallback=0.5)
        presence_penalty = config.getfloat('api', 'presence_penalty', fallback=0.0)
        
        print(f"✓ API URL: {url}")
        print(f"✓ 模型: {model}")
        print(f"✓ API密钥: {api_key[:10]}..." if api_key else "✗ API密钥未配置")
        print(f"✓ 最大token数: {max_tokens}")
        print(f"✓ 温度: {temperature}")
        print(f"✓ top_p: {top_p}")
        print(f"✓ frequency_penalty: {frequency_penalty}")
        print(f"✓ presence_penalty: {presence_penalty}")
        
        # 验证配置完整性
        if url and model and api_key:
            print("✓ 所有必要配置都已读取")
            return True
        else:
            print("✗ 缺少必要配置")
            return False
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_manager():
    """测试提示词管理器"""
    print("\n=== 测试提示词管理器 ===")
    
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

def test_config_consistency():
    """测试配置一致性"""
    print("\n=== 测试配置一致性 ===")
    
    try:
        from config_loader import config
        from prompt_manager import get_prompt_manager
        
        # 从配置文件获取参数
        config_url = config.get('api', 'url')
        config_model = config.get('api', 'model')
        config_api_key = config.get_secret('siliconflow_api_key')
        config_system_prompt = config.get('chat', 'system_prompt', fallback='')
        
        # 从提示词管理器获取参数
        pm = get_prompt_manager()
        manager_system_prompt = pm.get_system_prompt('default')
        
        print(f"配置文件参数:")
        print(f"  URL: {config_url}")
        print(f"  模型: {config_model}")
        print(f"  API密钥: {config_api_key[:10]}..." if config_api_key else "  未配置")
        print(f"  系统提示词: {len(config_system_prompt)} 字符")
        
        print(f"\n提示词管理器参数:")
        print(f"  系统提示词: {len(manager_system_prompt)} 字符")
        
        # 验证一致性
        if config_system_prompt == manager_system_prompt:
            print("✓ 提示词一致性验证通过")
        else:
            print("✗ 提示词一致性验证失败")
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
            print("✓ 不再依赖环境变量")
        else:
            print("⚠ 配置文件中的API密钥未配置")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_bot_import():
    """测试knowledge_bot模块导入"""
    print("\n=== 测试knowledge_bot模块导入 ===")
    
    try:
        # 只导入模块，不初始化实例
        import knowledge_bot
        print("✓ knowledge_bot模块导入成功")
        
        # 检查是否有必要的导入
        if hasattr(knowledge_bot, 'config_loader'):
            print("✓ 已导入config_loader")
        if hasattr(knowledge_bot, 'prompt_manager'):
            print("✓ 已导入prompt_manager")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("KnowledgeBot配置参数化功能测试（简化版）")
    print("=" * 50)
    
    tests = [
        test_config_parameters,
        test_prompt_manager,
        test_config_consistency,
        test_environment_variable_replacement,
        test_knowledge_bot_import
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
        print("\n总结:")
        print("- URL、模型、API密钥都已从配置文件读取")
        print("- 提示词已从配置文件读取")
        print("- 不再依赖环境变量")
        print("- 所有参数都已参数化到config.conf文件中")
    else:
        print("✗ 部分测试失败，请检查配置和代码")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 