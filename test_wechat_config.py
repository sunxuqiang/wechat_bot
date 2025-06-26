#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试微信机器人配置
验证所有硬编码参数是否已正确移动到config.conf
"""

import logging
from wechat_bot import WeChatBot
from config_loader import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_wechat_config_loading():
    """测试微信机器人配置加载"""
    print("=== 测试微信机器人配置加载 ===")
    
    try:
        # 创建微信机器人实例（但不启动）
        bot = WeChatBot()
        
        # 检查配置是否正确加载
        print("\n配置验证:")
        print(f"  最大重试次数: {bot.wechat_max_retries}")
        print(f"  重试延迟: {bot.wechat_retry_delay}秒")
        print(f"  最大Token数: {bot.wechat_max_tokens}")
        print(f"  温度参数: {bot.wechat_temperature}")
        print(f"  Top-p参数: {bot.wechat_top_p}")
        print(f"  频率惩罚: {bot.wechat_frequency_penalty}")
        print(f"  存在惩罚: {bot.wechat_presence_penalty}")
        print(f"  请求超时: {bot.wechat_timeout}秒")
        print(f"  知识库监控间隔: {bot.wechat_vector_store_watch_interval}秒")
        
        # 验证配置值
        expected_values = {
            'wechat_max_retries': 3,
            'wechat_retry_delay': 2,
            'wechat_max_tokens': 2048,
            'wechat_temperature': 0.7,
            'wechat_top_p': 0.7,
            'wechat_frequency_penalty': 0.5,
            'wechat_presence_penalty': 0.0,
            'wechat_timeout': 30,
            'wechat_vector_store_watch_interval': 30
        }
        
        print("\n配置验证结果:")
        all_correct = True
        for key, expected_value in expected_values.items():
            actual_value = getattr(bot, key)
            if actual_value == expected_value:
                print(f"  ✅ {key}: {actual_value}")
            else:
                print(f"  ❌ {key}: 期望 {expected_value}, 实际 {actual_value}")
                all_correct = False
        
        if all_correct:
            print("\n🎉 所有配置都正确加载！")
        else:
            print("\n⚠️ 部分配置加载不正确，请检查config.conf文件")
            
        return all_correct
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config_file_values():
    """测试config.conf文件中的值"""
    print("\n=== 测试config.conf文件值 ===")
    
    try:
        # 检查config.conf中的值
        expected_values = {
            'wechat_max_retries': 3,
            'wechat_retry_delay': 2,
            'wechat_max_tokens': 2048,
            'wechat_temperature': 0.7,
            'wechat_top_p': 0.7,
            'wechat_frequency_penalty': 0.5,
            'wechat_presence_penalty': 0.0,
            'wechat_timeout': 30,
            'wechat_vector_store_watch_interval': 30
        }
        
        print("config.conf文件验证:")
        all_correct = True
        for key, expected_value in expected_values.items():
            try:
                if isinstance(expected_value, int):
                    actual_value = config.getint('chat', key)
                elif isinstance(expected_value, float):
                    actual_value = config.getfloat('chat', key)
                else:
                    actual_value = config.get('chat', key)
                
                if actual_value == expected_value:
                    print(f"  ✅ {key}: {actual_value}")
                else:
                    print(f"  ❌ {key}: 期望 {expected_value}, 实际 {actual_value}")
                    all_correct = False
            except Exception as e:
                print(f"  ❌ {key}: 读取失败 - {str(e)}")
                all_correct = False
        
        if all_correct:
            print("\n🎉 config.conf文件配置正确！")
        else:
            print("\n⚠️ config.conf文件配置有问题")
            
        return all_correct
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试微信机器人配置...")
    
    # 测试配置加载
    config_loading_ok = test_wechat_config_loading()
    
    # 测试config.conf文件
    config_file_ok = test_config_file_values()
    
    print("\n" + "="*50)
    print("测试总结:")
    if config_loading_ok and config_file_ok:
        print("✅ 所有测试通过！微信机器人配置已成功从硬编码移动到config.conf")
        print("\n改进内容:")
        print("1. 重试参数 (max_retries, retry_delay)")
        print("2. 模型参数 (max_tokens, temperature, top_p, frequency_penalty, presence_penalty)")
        print("3. 超时参数 (timeout)")
        print("4. 监控间隔 (vector_store_watch_interval)")
        print("\n现在可以通过修改config.conf文件来调整这些参数，无需修改代码！")
    else:
        print("❌ 部分测试失败，请检查配置")
    
    print("="*50)

if __name__ == "__main__":
    main() 