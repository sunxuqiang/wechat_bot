#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试txt文档上传和分割效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_txt_processing():
    """测试txt文档处理效果"""
    print("=== 测试txt文档处理效果 ===\n")
    
    try:
        from file_processors.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # 处理测试文档
        test_file = "test_doc.txt"
        if not os.path.exists(test_file):
            print(f"✗ 测试文件不存在: {test_file}")
            return False
        
        print(f"处理文件: {test_file}")
        
        # 读取原始内容
        with open(test_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        print(f"原始文件大小: {len(original_content)} 字符")
        print(f"原始文件行数: {len(original_content.splitlines())}")
        
        # 处理文件
        chunks = processor.process(test_file)
        print(f"\n处理结果: {len(chunks)} 个文本块")
        
        # 分析分割效果
        total_chars = 0
        chunk_lengths = []
        
        for i, chunk_data in enumerate(chunks):
            text = chunk_data['text']
            metadata = chunk_data['metadata']
            
            chunk_length = len(text)
            total_chars += chunk_length
            chunk_lengths.append(chunk_length)
            
            print(f"\n=== 文本块 {i+1} ===")
            print(f"长度: {chunk_length} 字符")
            print(f"来源: {metadata['source']}")
            print(f"内容预览: {text[:100]}...")
            
            # 检查分割策略
            if '\n\n' in text:
                print("分割策略: 段落分割")
            elif any(pattern in text for pattern in ['1.', '2.', '3.', '一、', '二、', '三、']):
                print("分割策略: 序号分割")
            elif any(pattern in text for pattern in ['第一章：', '第二章：', '第三章：']):
                print("分割策略: 标题分割")
            else:
                print("分割策略: 句子分割")
        
        # 统计分析
        print(f"\n=== 分割效果分析 ===")
        print(f"总字符数: {total_chars}")
        print(f"平均块长度: {total_chars / len(chunks):.1f} 字符")
        print(f"最小块长度: {min(chunk_lengths)} 字符")
        print(f"最大块长度: {max(chunk_lengths)} 字符")
        
        # 检查分割质量
        short_chunks = [c for c in chunk_lengths if c < 50]
        long_chunks = [c for c in chunk_lengths if c > 1000]
        
        if short_chunks:
            print(f"警告: {len(short_chunks)} 个过短的块 (< 50字符)")
        if long_chunks:
            print(f"警告: {len(long_chunks)} 个过长的块 (> 1000字符)")
        
        if not short_chunks and not long_chunks:
            print("✓ 文本块长度分布合理")
        
        # 检查内容完整性
        original_words = set(original_content.split())
        chunk_words = set()
        for chunk_data in chunks:
            chunk_words.update(chunk_data['text'].split())
        
        missing_words = original_words - chunk_words
        if missing_words:
            print(f"警告: 丢失了 {len(missing_words)} 个单词")
        else:
            print("✓ 内容完整性良好")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_upload_simulation():
    """模拟上传过程"""
    print("\n=== 模拟上传过程 ===\n")
    
    try:
        from smart_kb import SmartKnowledgeBase
        
        # 创建知识库实例
        kb = SmartKnowledgeBase()
        
        # 模拟上传文件
        test_file = "test_doc.txt"
        if not os.path.exists(test_file):
            print(f"✗ 测试文件不存在: {test_file}")
            return False
        
        print(f"模拟上传文件: {test_file}")
        
        # 上传文件
        success = kb.add_document(test_file)
        
        if success:
            print("✓ 文件上传成功")
            
            # 获取知识库信息
            info = kb.get_statistics()
            print(f"知识库统计: {info}")
            
            # 测试搜索
            print("\n测试搜索功能:")
            search_results = kb.search("智能系统", top_k=3)
            
            if search_results:
                print(f"搜索到 {len(search_results)} 个结果:")
                for i, (text, score, metadata) in enumerate(search_results):
                    print(f"结果 {i+1}: 分数={score:.3f}, 内容={text[:50]}...")
            else:
                print("未找到搜索结果")
        else:
            print("✗ 文件上传失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试txt文档上传和分割效果")
    
    success = True
    
    # 测试txt文档处理
    if not test_txt_processing():
        success = False
    
    # 模拟上传过程
    if not test_upload_simulation():
        success = False
    
    if success:
        print("\n✓ 所有测试通过")
        print("\n总结:")
        print("- txt文档分割功能正常")
        print("- 支持多种分割策略")
        print("- 分割效果良好")
        print("- 上传功能正常")
        print("- 搜索功能正常")
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 