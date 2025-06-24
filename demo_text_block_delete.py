#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本块删除功能演示
"""

import requests
import json
import time

def login_and_get_session():
    """登录并获取会话"""
    base_url = "http://localhost:5000"
    
    # 创建会话
    session = requests.Session()
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin'
    }
    
    try:
        response = session.post(f"{base_url}/login", data=login_data)
        if response.status_code == 200:
            print("✓ 登录成功")
            return session
        else:
            print(f"✗ 登录失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ 登录异常: {str(e)}")
        return None

def demo_text_block_delete():
    """演示文本块删除功能"""
    print("=== 文本块删除功能演示 ===\n")
    
    base_url = "http://localhost:5000"
    
    # 登录获取会话
    session = login_and_get_session()
    if not session:
        print("无法登录，演示结束")
        return
    
    # 1. 获取当前文本块列表
    print("1. 获取当前文本块列表...")
    try:
        response = session.get(f"{base_url}/api/text_blocks")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✓ 成功获取文本块列表")
                print(f"  总数量: {data['total']}")
                print(f"  当前页: {data['page']}")
                print(f"  每页大小: {data['size']}")
                
                # 显示前几个文本块
                print("\n  前3个文本块:")
                for i, block in enumerate(data['text_blocks'][:3]):
                    print(f"    {i+1}. ID: {block['id']}, 内容预览: {block['content'][:50]}...")
                
                if len(data['text_blocks']) > 0:
                    # 2. 演示单个删除
                    first_block_id = data['text_blocks'][0]['id']
                    print(f"\n2. 演示单个删除 (ID: {first_block_id})...")
                    print("   注意: 这只是演示，不会实际删除")
                    print(f"   删除API: DELETE {base_url}/api/text_blocks/{first_block_id}")
                    
                    # 3. 演示批量删除
                    if len(data['text_blocks']) >= 2:
                        block_ids = [data['text_blocks'][0]['id'], data['text_blocks'][1]['id']]
                        print(f"\n3. 演示批量删除 (IDs: {block_ids})...")
                        print("   注意: 这只是演示，不会实际删除")
                        print(f"   批量删除API: POST {base_url}/api/text_blocks/batch_delete")
                        print(f"   请求体: {json.dumps({'ids': block_ids}, ensure_ascii=False)}")
                
            else:
                print(f"✗ 获取文本块列表失败: {data.get('message', '未知错误')}")
        else:
            print(f"✗ HTTP请求失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到应用服务器")
        print("  请确保应用正在运行: python app.py")
    except Exception as e:
        print(f"✗ 演示失败: {str(e)}")
    
    print("\n=== 前端功能说明 ===")
    print("1. 访问文本块查询页面: http://localhost:5000/text-blocks")
    print("2. 使用复选框选择要删除的文本块")
    print("3. 点击'批量删除'按钮进行批量删除")
    print("4. 或点击单个文本块的'删除'按钮进行单个删除")
    print("5. 所有删除操作都有确认对话框")
    
    print("\n=== 安全提示 ===")
    print("• 删除操作不可恢复，请谨慎操作")
    print("• 建议在删除前备份向量存储文件")
    print("• 大量删除操作可能影响系统性能")

if __name__ == "__main__":
    demo_text_block_delete() 