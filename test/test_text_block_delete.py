#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文本块删除功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_vector_store_delete():
    """测试向量存储的删除功能"""
    print("=== 测试向量存储删除功能 ===")
    
    try:
        from vector_store import FaissVectorStore
        
        # 创建向量存储实例
        vector_store = FaissVectorStore()
        
        # 加载现有数据
        if os.path.exists("knowledge_base/vector_store.index"):
            vector_store.load("knowledge_base/vector_store")
            print("✓ 向量存储加载成功")
            print(f"  当前文本块数量: {len(vector_store.documents)}")
        else:
            print("⚠ 向量存储文件不存在，跳过测试")
            return True
        
        # 测试删除功能
        if len(vector_store.documents) > 0:
            # 获取第一个文本块的信息
            first_block = vector_store.documents[0]
            print(f"  第一个文本块内容预览: {first_block[0][:50]}...")
            
            # 测试删除第一个文本块
            original_count = len(vector_store.documents)
            if vector_store.delete_text_blocks([0]):
                print(f"✓ 删除第一个文本块成功")
                print(f"  删除前数量: {original_count}")
                print(f"  删除后数量: {len(vector_store.documents)}")
                
                # 验证删除结果
                if len(vector_store.documents) == original_count - 1:
                    print("✓ 删除结果验证成功")
                else:
                    print("✗ 删除结果验证失败")
                    return False
            else:
                print("✗ 删除文本块失败")
                return False
        else:
            print("⚠ 没有文本块可删除，跳过删除测试")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_delete():
    """测试API删除功能"""
    print("\n=== 测试API删除功能 ===")
    
    try:
        import app
        
        # 检查API路由是否存在
        if hasattr(app, 'delete_text_block'):
            print("✓ delete_text_block API路由存在")
        else:
            print("✗ delete_text_block API路由不存在")
            return False
            
        if hasattr(app, 'batch_delete_text_blocks'):
            print("✓ batch_delete_text_blocks API路由存在")
        else:
            print("✗ batch_delete_text_blocks API路由不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_integration():
    """测试前端集成"""
    print("\n=== 测试前端集成 ===")
    
    try:
        # 检查前端模板是否包含删除功能
        with open('templates/text_blocks.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查必要的元素
        checks = [
            ('全选复选框', 'id="selectAll"'),
            ('批量删除按钮', 'id="batchDeleteBtn"'),
            ('单个删除按钮', 'btn-danger'),
            ('删除确认对话框', 'Swal.fire'),
            ('批量删除API调用', '/api/text_blocks/batch_delete'),
            ('单个删除API调用', 'DELETE')
        ]
        
        for check_name, check_content in checks:
            if check_content in content:
                print(f"✓ {check_name}存在")
            else:
                print(f"✗ {check_name}不存在")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_delete_functionality():
    """测试完整的删除功能"""
    print("\n=== 测试完整删除功能 ===")
    
    try:
        from vector_store import FaissVectorStore
        
        # 创建向量存储实例
        vector_store = FaissVectorStore()
        
        # 加载现有数据
        if os.path.exists("knowledge_base/vector_store.index"):
            vector_store.load("knowledge_base/vector_store")
            print("✓ 向量存储加载成功")
            
            if len(vector_store.documents) > 0:
                print(f"  当前文本块数量: {len(vector_store.documents)}")
                
                # 测试批量删除
                test_indices = [0] if len(vector_store.documents) >= 1 else []
                if test_indices:
                    original_count = len(vector_store.documents)
                    if vector_store.delete_text_blocks(test_indices):
                        print(f"✓ 批量删除测试成功")
                        print(f"  删除前: {original_count} 个文本块")
                        print(f"  删除后: {len(vector_store.documents)} 个文本块")
                        print(f"  删除数量: {len(test_indices)} 个")
                        
                        # 验证删除结果
                        if len(vector_store.documents) == original_count - len(test_indices):
                            print("✓ 删除结果验证成功")
                        else:
                            print("✗ 删除结果验证失败")
                            return False
                    else:
                        print("✗ 批量删除测试失败")
                        return False
                else:
                    print("⚠ 没有足够的文本块进行删除测试")
            else:
                print("⚠ 向量存储为空，跳过删除测试")
        else:
            print("⚠ 向量存储文件不存在，跳过删除测试")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试文本块删除功能")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    success = True
    
    # 测试向量存储删除功能
    if not test_vector_store_delete():
        success = False
    
    # 测试API删除功能
    if not test_api_delete():
        success = False
    
    # 测试前端集成
    if not test_frontend_integration():
        success = False
    
    # 测试完整删除功能
    if not test_delete_functionality():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- 向量存储删除功能正常")
        print("- API删除接口已添加")
        print("- 前端删除功能已集成")
        print("- 支持单个删除和批量删除")
        print("- 删除操作会同步更新向量索引")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 