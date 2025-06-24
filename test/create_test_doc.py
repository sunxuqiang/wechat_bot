#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试.doc文件或使用现有文件进行测试
"""

import os
import shutil

def create_test_doc():
    """创建测试.doc文件"""
    # 确保目录存在
    os.makedirs("uploads/word", exist_ok=True)
    
    # 检查是否有现有的.docx文件可以复制
    docx_file = "uploads/word/test.docx"
    doc_file = "uploads/word/test.doc"
    
    if os.path.exists(docx_file):
        print(f"发现现有的.docx文件: {docx_file}")
        print("复制为.doc文件进行测试...")
        
        # 复制.docx文件为.doc文件（用于测试错误处理）
        shutil.copy2(docx_file, doc_file)
        print(f"已创建测试.doc文件: {doc_file}")
        print(f"文件大小: {os.path.getsize(doc_file)} 字节")
        
        return doc_file
    else:
        print("没有找到现有的.docx文件")
        print("请先运行 create_test_word.py 创建.docx文件")
        return None

if __name__ == "__main__":
    create_test_doc() 