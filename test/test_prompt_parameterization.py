#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试提示词参数化功能
验证所有提示词都能从配置文件正确读取和使用
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

def test_prompt_manager():
    """测试提示词管理器"""
    print("=== 测试提示词管理器 ===")
    
    try:
        from prompt_manager import get_prompt_manager
        
        # 获取提示词管理器实例
        pm = get_prompt_manager()
        print("✓ 提示词管理器初始化成功")
        
        # 测试获取所有提示词
        all_prompts = pm.get_all_prompts()
        print(f"✓ 获取到 {len(all_prompts)} 个提示词")
        
        for name, content in all_prompts.items():
            print(f"  {name}: {len(content)} 字符")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_system_prompts():
    """测试系统提示词"""
    print("\n=== 测试系统提示词 ===")
    
    try:
        from prompt_manager import get_prompt_manager
        
        pm = get_prompt_manager()
        
        # 测试默认系统提示词
        default_prompt = pm.get_system_prompt('default')
        print(f"✓ 默认系统提示词: {len(default_prompt)} 字符")
        print(f"  预览: {default_prompt[:100]}...")
        
        # 测试微信系统提示词
        wechat_prompt = pm.get_system_prompt('wechat')
        print(f"✓ 微信系统提示词: {len(wechat_prompt)} 字符")
        print(f"  预览: {wechat_prompt[:100]}...")
        
        # 验证提示词不同
        if default_prompt != wechat_prompt:
            print("✓ 默认和微信系统提示词不同（符合预期）")
        else:
            print("⚠ 默认和微信系统提示词相同")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_prompt_formatting():
    """测试用户提示词格式化"""
    print("\n=== 测试用户提示词格式化 ===")
    
    try:
        from prompt_manager import get_prompt_manager
        
        pm = get_prompt_manager()
        
        # 测试用户提示词模板
        template = pm.get_user_prompt_template()
        print(f"✓ 用户提示词模板: {len(template)} 字符")
        print(f"  模板: {template}")
        
        # 测试格式化
        test_message = "这是一个测试问题"
        test_context = "这是知识库上下文"
        test_history = "用户：之前的问题\n助手：之前的回答"
        
        formatted = pm.format_user_prompt(
            message=test_message,
            context=test_context,
            history=test_history
        )
        
        print(f"✓ 格式化成功: {len(formatted)} 字符")
        print(f"  格式化结果: {formatted}")
        
        # 验证变量替换
        if test_message in formatted and test_context in formatted and test_history in formatted:
            print("✓ 变量替换正确")
        else:
            print("✗ 变量替换失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_chunking_prompt():
    """测试AI分块提示词"""
    print("\n=== 测试AI分块提示词 ===")
    
    try:
        from prompt_manager import get_prompt_manager
        
        pm = get_prompt_manager()
        
        # 获取AI分块提示词
        chunk_prompt = pm.get_ai_chunking_prompt()
        print(f"✓ AI分块提示词: {len(chunk_prompt)} 字符")
        print(f"  预览: {chunk_prompt[:200]}...")
        
        # 验证包含必要占位符
        if '{text}' in chunk_prompt:
            print("✓ 包含 {text} 占位符")
        else:
            print("✗ 缺少 {text} 占位符")
            return False
        
        # 验证包含JSON格式要求
        if 'JSON' in chunk_prompt and 'chunks' in chunk_prompt:
            print("✓ 包含JSON格式要求")
        else:
            print("⚠ 可能缺少JSON格式要求")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_wechat_bot_integration():
    """测试微信机器人集成"""
    print("\n=== 测试微信机器人集成 ===")
    
    try:
        import wechat_bot
        
        # 检查提示词管理器是否已导入
        if hasattr(wechat_bot, 'prompt_manager'):
            print("✓ 微信机器人已集成提示词管理器")
            
            # 测试系统提示词获取
            system_prompt = wechat_bot.prompt_manager.get_system_prompt('wechat')
            print(f"✓ 微信机器人系统提示词: {len(system_prompt)} 字符")
            
            # 测试用户提示词格式化
            formatted = wechat_bot.prompt_manager.format_user_prompt(
                message="测试消息",
                context="测试上下文",
                history="测试历史"
            )
            print(f"✓ 微信机器人用户提示词格式化: {len(formatted)} 字符")
            
        else:
            print("✗ 微信机器人未集成提示词管理器")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_chunk_service_integration():
    """测试AI分块服务集成"""
    print("\n=== 测试AI分块服务集成 ===")
    
    try:
        from ai_chunk_service import AIChunkService
        
        # 创建AI分块服务实例
        service = AIChunkService()
        print("✓ AI分块服务初始化成功")
        
        # 检查提示词管理器集成
        if hasattr(service, 'prompt_manager'):
            print("✓ AI分块服务已集成提示词管理器")
            
            # 测试分块提示词获取
            chunk_prompt = service.chunk_prompt
            print(f"✓ AI分块提示词: {len(chunk_prompt)} 字符")
            
            # 验证提示词包含必要内容
            if '{text}' in chunk_prompt:
                print("✓ 分块提示词包含 {text} 占位符")
            else:
                print("✗ 分块提示词缺少 {text} 占位符")
                return False
                
        else:
            print("✗ AI分块服务未集成提示词管理器")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config_file_prompts():
    """测试配置文件中的提示词"""
    print("\n=== 测试配置文件中的提示词 ===")
    
    try:
        from config_loader import config
        
        # 测试基础系统提示词
        system_prompt = config.get('chat', 'system_prompt', fallback='')
        print(f"✓ 配置文件系统提示词: {len(system_prompt)} 字符")
        
        # 测试微信系统提示词
        wechat_system_prompt = config.get('chat', 'wechat_system_prompt', fallback='')
        print(f"✓ 配置文件微信系统提示词: {len(wechat_system_prompt)} 字符")
        
        # 测试用户提示词模板
        user_prompt_template = config.get('chat', 'user_prompt_template', fallback='')
        print(f"✓ 配置文件用户提示词模板: {len(user_prompt_template)} 字符")
        
        # 验证配置完整性
        if system_prompt and wechat_system_prompt and user_prompt_template:
            print("✓ 配置文件中的提示词配置完整")
        else:
            print("⚠ 配置文件中的提示词配置可能不完整")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("提示词参数化功能测试")
    print("=" * 50)
    
    tests = [
        test_prompt_manager,
        test_system_prompts,
        test_user_prompt_formatting,
        test_ai_chunking_prompt,
        test_wechat_bot_integration,
        test_ai_chunk_service_integration,
        test_config_file_prompts
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
        print("✓ 所有测试通过！提示词参数化功能正常")
    else:
        print("✗ 部分测试失败，请检查配置和代码")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 