#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查第一章分块问题
"""

from ai_chunk_service import AIChunkService

def test_chapter1_issue():
    """检查第一章分块问题"""
    print("=== 检查第一章分块问题 ===\n")
    
    # 读取test_doc.txt文件
    with open('test_doc.txt', 'r', encoding='utf-8') as f:
        test_text = f.read()
    
    # 提取第一章的原始内容
    print("原始第一章内容:")
    lines = test_text.split('\n')
    chapter1_content = []
    in_chapter1 = False
    
    for line in lines:
        if line.strip() == "第一章：系统概述":
            in_chapter1 = True
            chapter1_content.append(line)
        elif in_chapter1 and line.strip() == "第二章：安装配置":
            break
        elif in_chapter1:
            chapter1_content.append(line)
    
    chapter1_text = '\n'.join(chapter1_content)
    print(f"第一章完整内容 ({len(chapter1_text)} 字符):")
    print("=" * 50)
    print(chapter1_text)
    print("=" * 50)
    
    # 测试AI分块
    print("\n=== AI分块结果 ===")
    service = AIChunkService()
    chunks = service.chunk_with_ai(test_text)
    
    if chunks:
        print(f"AI分块成功，返回 {len(chunks)} 个chunks")
        
        # 查找包含第一章内容的chunks
        chapter1_chunks = []
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            if '第一章' in content or '系统概述' in content or '系统特点' in content:
                chapter1_chunks.append((i+1, chunk))
        
        print(f"\n包含第一章内容的chunks ({len(chapter1_chunks)} 个):")
        for i, (chunk_num, chunk) in enumerate(chapter1_chunks):
            print(f"\n块 {chunk_num}:")
            print(f"  类型: {chunk.get('type', '未知')}")
            print(f"  摘要: {chunk.get('summary', '无')}")
            print(f"  内容长度: {len(chunk.get('content', ''))} 字符")
            print(f"  内容: {chunk.get('content', '')}")
        
        # 检查是否所有第一章内容都被包含
        all_chapter1_content = ' '.join([chunk.get('content', '') for chunk_num, chunk in chapter1_chunks])
        missing_parts = []
        
        # 检查关键内容是否缺失
        key_parts = [
            "第一章：系统概述",
            "本智能系统是一款基于人工智能技术的知识管理平台",
            "系统特点：",
            "智能文档处理",
            "高效搜索功能", 
            "用户友好界面"
        ]
        
        for part in key_parts:
            if part not in all_chapter1_content:
                missing_parts.append(part)
        
        if missing_parts:
            print(f"\n❌ 缺失的内容: {missing_parts}")
        else:
            print(f"\n✅ 第一章内容完整")
        
        # 检查分块是否合理
        if len(chapter1_chunks) > 1:
            print(f"\n⚠️  第一章被分成了 {len(chapter1_chunks)} 个块，可能不够完整")
        else:
            print(f"\n✅ 第一章作为一个完整块处理")
            
    else:
        print("❌ AI分块失败")

if __name__ == "__main__":
    test_chapter1_issue() 