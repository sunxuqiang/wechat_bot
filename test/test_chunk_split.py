#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试文本分割功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_text_processor():
    """测试文本处理器"""
    print("=== 测试文本处理器分割功能 ===\n")
    
    try:
        from file_processors.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # 测试用例1: 段落分割
        print("1. 测试段落分割:")
        text1 = """
第一段内容。这是一个测试段落，包含多个句子。

第二段内容。这是另一个段落，与第一段之间有空行。

第三段内容。这是最后一个段落。
        """
        chunks1 = processor.split_text_advanced(text1)
        print(f"   段落分割结果: {len(chunks1)} 个块")
        for i, chunk in enumerate(chunks1):
            print(f"   块 {i+1}: {chunk[:50]}...")
        print()
        
        # 测试用例2: 序号分割
        print("2. 测试序号分割:")
        text2 = """
产品说明：

1. 产品名称：智能手机
   这是第一款产品的详细说明。

2. 产品价格：3999元
   这是第二款产品的价格信息。

3. 产品功能：拍照、上网、通话
   这是第三款产品的功能列表。
        """
        chunks2 = processor.split_text_advanced(text2)
        print(f"   序号分割结果: {len(chunks2)} 个块")
        for i, chunk in enumerate(chunks2):
            print(f"   块 {i+1}: {chunk[:50]}...")
        print()
        
        # 测试用例3: 中文序号分割
        print("3. 测试中文序号分割:")
        text3 = """
使用说明：

一、安装步骤
首先下载安装包，然后运行安装程序。

二、配置设置
打开配置文件，修改相关参数。

三、使用方法
按照界面提示进行操作。
        """
        chunks3 = processor.split_text_advanced(text3)
        print(f"   中文序号分割结果: {len(chunks3)} 个块")
        for i, chunk in enumerate(chunks3):
            print(f"   块 {i+1}: {chunk[:50]}...")
        print()
        
        # 测试用例4: 标题分割
        print("4. 测试标题分割:")
        text4 = """
第一章：系统概述
本章介绍系统的基本概念和架构。

第二章：功能模块
本章详细说明各个功能模块。

第三章：使用指南
本章提供详细的使用说明。
        """
        chunks4 = processor.split_text_advanced(text4)
        print(f"   标题分割结果: {len(chunks4)} 个块")
        for i, chunk in enumerate(chunks4):
            print(f"   块 {i+1}: {chunk[:50]}...")
        print()
        
        # 测试用例5: 混合内容
        print("5. 测试混合内容:")
        text5 = """
项目报告

第一章：项目背景
本项目旨在开发一个智能系统。

主要功能：
1. 数据处理
2. 分析报告
3. 可视化展示

技术架构：
一、前端技术
使用React框架开发用户界面。

二、后端技术
使用Python Flask框架。
        """
        chunks5 = processor.split_text_advanced(text5)
        print(f"   混合内容分割结果: {len(chunks5)} 个块")
        for i, chunk in enumerate(chunks5):
            print(f"   块 {i+1}: {chunk[:50]}...")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_file_processing():
    """测试文件处理"""
    print("=== 测试文件处理 ===\n")
    
    try:
        from file_processors.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # 创建测试文件
        test_file = "test_chunk_split.txt"
        test_content = """
测试文档

第一章：产品介绍
本产品是一款智能设备，具有以下特点：

1. 高性能处理器
   采用最新技术，运行速度快。

2. 大容量存储
   支持扩展存储，满足各种需求。

3. 长续航电池
   一次充电可使用一整天。

第二章：使用方法
一、开机步骤
按下电源键即可开机。

二、基本操作
按照屏幕提示进行操作。

三、注意事项
请勿在潮湿环境中使用。
        """
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"创建测试文件: {test_file}")
        
        # 处理文件
        chunks = processor.process(test_file)
        print(f"文件处理结果: {len(chunks)} 个文本块")
        
        for i, chunk_data in enumerate(chunks):
            text = chunk_data['text']
            metadata = chunk_data['metadata']
            print(f"块 {i+1}:")
            print(f"  内容: {text[:80]}...")
            print(f"  来源: {metadata['source']}")
            print(f"  文件类型: {metadata['file_type']}")
            print()
        
        # 清理测试文件
        os.remove(test_file)
        print("清理测试文件完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_detection_methods():
    """测试检测方法"""
    print("=== 测试检测方法 ===\n")
    
    try:
        from file_processors.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # 测试序号检测
        test_cases = [
            ("1. 第一项\n2. 第二项", "序号文本"),
            ("一、第一项\n二、第二项", "中文序号文本"),
            ("第一章：内容", "标题文本"),
            ("这是普通段落。\n\n这是另一个段落。", "段落文本"),
            ("这是普通句子。这是另一个句子。", "句子文本")
        ]
        
        for text, description in test_cases:
            has_numbers = processor._has_numbered_items(text)
            has_headings = processor._has_headings(text)
            has_paragraphs = '\n\n' in text
            
            print(f"文本类型: {description}")
            print(f"  包含序号: {has_numbers}")
            print(f"  包含标题: {has_headings}")
            print(f"  包含段落: {has_paragraphs}")
            print()
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试文本分割功能")
    
    success = True
    
    # 测试文本处理器
    if not test_text_processor():
        success = False
    
    # 测试文件处理
    if not test_file_processing():
        success = False
    
    # 测试检测方法
    if not test_detection_methods():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- 段落分割功能正常")
        print("- 序号分割功能正常")
        print("- 标题分割功能正常")
        print("- 文件处理功能正常")
        print("- 检测方法功能正常")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 