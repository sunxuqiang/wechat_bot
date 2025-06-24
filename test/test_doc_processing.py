#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试.doc文件处理
"""

import os
import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_doc_processing():
    """测试.doc文件处理"""
    print("=== 测试.doc文件处理 ===")
    
    # 测试文件路径
    test_files = [
        "uploads/word/test.doc",
        "uploads/word/20254.doc",  # 这个文件在错误日志中出现
    ]
    
    for file_path in test_files:
        print(f"\n--- 测试文件: {file_path} ---")
        
        # 检查文件是否存在
        if os.path.exists(file_path):
            print(f"文件存在: {file_path}")
            print(f"文件大小: {os.path.getsize(file_path)} 字节")
            
            # 测试不同的读取方法
            test_read_methods(file_path)
        else:
            print(f"文件不存在: {file_path}")
    
    print("\n=== 测试完成 ===")

def test_read_methods(file_path):
    """测试不同的.doc文件读取方法"""
    
    # 方法1: docx2txt
    print("\n1. 测试 docx2txt:")
    try:
        import docx2txt
        content = docx2txt.process(file_path)
        if content and content.strip():
            print("✓ docx2txt 成功")
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容预览: {content[:100]}...")
        else:
            print("✗ docx2txt 返回空内容")
    except Exception as e:
        print(f"✗ docx2txt 失败: {str(e)}")
    
    # 方法2: mammoth
    print("\n2. 测试 mammoth:")
    try:
        import mammoth
        with open(file_path, "rb") as docx_file:
            result = mammoth.extract_raw_text(docx_file)
            if result.value and result.value.strip():
                print("✓ mammoth 成功")
                print(f"  内容长度: {len(result.value)} 字符")
                print(f"  内容预览: {result.value[:100]}...")
            else:
                print("✗ mammoth 返回空内容")
    except ImportError:
        print("✗ mammoth 库未安装")
    except Exception as e:
        print(f"✗ mammoth 失败: {str(e)}")
    
    # 方法3: antiword (如果可用)
    print("\n3. 测试 antiword:")
    try:
        import subprocess
        result = subprocess.run(['antiword', file_path], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            print("✓ antiword 成功")
            print(f"  内容长度: {len(result.stdout)} 字符")
            print(f"  内容预览: {result.stdout[:100]}...")
        else:
            print("✗ antiword 返回空内容或失败")
    except (ImportError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"✗ antiword 不可用: {str(e)}")
    
    # 方法4: catdoc (如果可用)
    print("\n4. 测试 catdoc:")
    try:
        import subprocess
        result = subprocess.run(['catdoc', file_path], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            print("✓ catdoc 成功")
            print(f"  内容长度: {len(result.stdout)} 字符")
            print(f"  内容预览: {result.stdout[:100]}...")
        else:
            print("✗ catdoc 返回空内容或失败")
    except (ImportError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"✗ catdoc 不可用: {str(e)}")

if __name__ == "__main__":
    test_doc_processing() 