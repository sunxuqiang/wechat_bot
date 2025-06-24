#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Word文件处理器
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

from file_processors.word_processor import WordProcessor

def test_word_processor():
    """测试Word处理器"""
    print("=== 测试Word文件处理器 ===")
    
    # 创建处理器实例
    processor = WordProcessor()
    print(f"支持的扩展名: {processor.supported_extensions}")
    
    # 测试文件路径
    test_files = [
        "uploads/word/test.docx",
        "uploads/word/test.doc",
        "uploads/word/20254.doc"  # 这个文件在错误日志中出现
    ]
    
    for file_path in test_files:
        print(f"\n--- 测试文件: {file_path} ---")
        
        # 检查文件是否存在
        if os.path.exists(file_path):
            print(f"文件存在: {file_path}")
            print(f"文件大小: {os.path.getsize(file_path)} 字节")
            
            # 检查是否可以处理
            if processor.can_process(file_path):
                print("处理器支持此文件类型")
                
                try:
                    # 尝试处理文件
                    chunks = processor.process(file_path)
                    print(f"处理成功，生成了 {len(chunks)} 个文本块")
                    
                    # 显示前几个块的内容
                    for i, chunk in enumerate(chunks[:3]):
                        print(f"块 {i+1}:")
                        print(f"  内容: {chunk.get('text', '')[:100]}...")
                        print(f"  元数据: {chunk.get('metadata', {})}")
                        
                except Exception as e:
                    print(f"处理失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("处理器不支持此文件类型")
        else:
            print(f"文件不存在: {file_path}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_word_processor() 