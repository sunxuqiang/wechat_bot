#!/usr/bin/env python3
"""
测试权限管理功能
"""

import requests
import json

def test_permission_management():
    """测试权限管理功能"""
    base_url = "http://localhost:5000"
    
    # 1. 登录管理员账户
    print("1. 登录管理员账户...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'  # 根据实际配置调整
    }
    
    session = requests.Session()
    response = session.post(f"{base_url}/login", data=login_data)
    
    if response.status_code != 200:
        print(f"登录失败: {response.status_code}")
        return
    
    print("登录成功")
    
    # 2. 获取用户列表
    print("\n2. 获取用户列表...")
    response = session.get(f"{base_url}/api/users")
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text[:200]}...")  # 只显示前200个字符
    
    if response.status_code == 200:
        try:
            users = response.json()
            print(f"用户列表: {json.dumps(users, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return
    else:
        print(f"获取用户列表失败: {response.status_code}")
        print(response.text)
        return
    
    # 3. 测试权限管理页面
    print("\n3. 访问权限管理页面...")
    response = session.get(f"{base_url}/permission_management")
    
    if response.status_code == 200:
        print("权限管理页面访问成功")
        # 检查页面内容是否包含用户信息
        if "用户权限管理" in response.text:
            print("页面内容正确")
        else:
            print("页面内容异常")
    else:
        print(f"权限管理页面访问失败: {response.status_code}")
        print(response.text)
    
    # 4. 测试权限更新API
    if len(users) > 1:  # 如果有非管理员用户
        test_user = None
        for user in users:
            if user['username'] != 'admin':
                test_user = user
                break
        
        if test_user:
            print(f"\n4. 测试权限更新API (用户: {test_user['username']})...")
            
            # 更新上传权限
            update_data = {
                'username': test_user['username'],
                'permission': 'upload',
                'value': False
            }
            
            response = session.post(f"{base_url}/api/permissions", 
                                  json=update_data,
                                  headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                print(f"权限更新成功: {result}")
            else:
                print(f"权限更新失败: {response.status_code}")
                print(response.text)
    
    print("\n测试完成")

if __name__ == "__main__":
    test_permission_management() 