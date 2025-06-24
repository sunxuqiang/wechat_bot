#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试按章节分块的效果
验证修改后的AI分块服务
"""

from ai_chunk_service import AIChunkService

def test_chapter_chunk():
    """测试按章节分块的效果"""
    print("=== 测试按章节分块的效果 ===\n")
    
    # 读取test_doc.txt文件
    with open('test_doc.txt', 'r', encoding='utf-8') as f:
        test_text = f.read()
    
    print(f"文档长度: {len(test_text)} 字符")
    print(f"文档预览: {test_text[:100]}...\n")
    
    service = AIChunkService()
    
    # 执行AI分块
    print("开始AI分块...")
    chunks = service.chunk_with_ai(test_text)
    
    if chunks:
        print(f"\n✅ AI分块成功，生成 {len(chunks)} 个文本块")
        print("\n分块详情:")
        for i, chunk in enumerate(chunks):
            print(f"  块 {i+1}:")
            print(f"    类型: {chunk.get('type', '未知')}")
            print(f"    摘要: {chunk.get('summary', '无')}")
            print(f"    内容预览: {chunk.get('content', '')[:100]}...")
            print(f"    长度: {len(chunk.get('content', ''))} 字符")
            print()
        
        # 验证是否符合章节分块要求
        print("=== 分块验证 ===")
        expected_chunks = 7  # 标题 + 5个章节 + 结语
        if len(chunks) == expected_chunks:
            print(f"✅ 分块数量正确: {len(chunks)} 个块")
        else:
            print(f"⚠️  分块数量不符合预期: 期望 {expected_chunks} 个块，实际 {len(chunks)} 个块")
        
        # 检查块类型
        chunk_types = [chunk.get('type', '未知') for chunk in chunks]
        print(f"块类型分布: {chunk_types}")
        
        # 检查是否包含所有章节
        content_text = ' '.join([chunk.get('content', '') for chunk in chunks])
        chapters = ['第一章', '第二章', '第三章', '第四章', '第五章']
        missing_chapters = [ch for ch in chapters if ch not in content_text]
        if not missing_chapters:
            print("✅ 包含所有5个章节")
        else:
            print(f"⚠️  缺少章节: {missing_chapters}")
            
    else:
        print("\n❌ AI分块失败")

if __name__ == "__main__":
    test_chapter_chunk() 