#!/usr/bin/env python3
"""
测试向量存储加载和搜索功能
"""

from vector_store import FaissVectorStore

def test_vector_store():
    print("初始化向量存储...")
    vs = FaissVectorStore()
    
    print("加载向量存储...")
    vs.load('knowledge_base/vector_store')
    
    print(f"文档数量: {len(vs.documents)}")
    
    if len(vs.documents) > 0:
        print("\n前3个文档预览:")
        for i, (text, meta) in enumerate(vs.documents[:3]):
            print(f"{i+1}. {text[:100]}...")
            print(f"   元数据: {meta}")
            print()
    
    # 测试搜索功能
    print("测试搜索功能...")
    test_queries = ["智能手机", "手机", "智能", "系统"]
    
    for query in test_queries:
        print(f"\n搜索查询: '{query}'")
        results = vs.search(query, top_k=5)
        
        if results:
            print(f"找到 {len(results)} 个结果:")
            for i, (text, score, metadata) in enumerate(results):
                print(f"  {i+1}. 分数: {score:.4f}")
                print(f"     内容: {text[:100]}...")
                if '_debug_info' in metadata:
                    print(f"     调试信息: {metadata['_debug_info']}")
                print()
        else:
            print("未找到相关结果")
    
    # 检查搜索阈值设置
    print(f"\n当前搜索阈值设置:")
    print(f"  similarity_threshold: {vs.similarity_threshold}")
    print(f"  关键词匹配阈值: 0.3")
    print(f"  加权分数阈值: 0.4")

if __name__ == "__main__":
    test_vector_store() 