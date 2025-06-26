#!/usr/bin/env python3
"""
测试提示词管理API
"""

import requests
import json

def test_prompt_api():
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # 先登录获取session
    print("正在登录...")
    try:
        # 获取登录页面以获取CSRF token
        login_page = session.get(f"{base_url}/login")
        print(f"登录页面状态码: {login_page.status_code}")
        
        # 执行登录
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        login_response = session.post(
            f"{base_url}/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"登录状态码: {login_response.status_code}")
        print(f"登录响应: {login_response.text}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                print("登录成功！")
            else:
                print(f"登录失败: {login_result.get('message')}")
                return
        else:
            print("登录失败")
            return
            
    except Exception as e:
        print(f"登录请求失败: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # 测试获取配置
    print("测试获取提示词配置...")
    try:
        response = session.get(f"{base_url}/api/config/prompt")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功获取配置: {data}")
            if data.get('success') and data.get('data', {}).get('ai_chunking_prompt'):
                print("✓ 提示词内容已加载")
            else:
                print("✗ 提示词内容为空")
        else:
            print(f"获取配置失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试重置配置
    print("测试重置提示词配置...")
    try:
        response = session.post(f"{base_url}/api/config/prompt/reset")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功重置配置: {data}")
        else:
            print(f"重置配置失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_prompt_api() 