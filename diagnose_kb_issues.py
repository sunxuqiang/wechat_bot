#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断知识库问题脚本
检查文档数量问题和微信端查询问题
"""

import sys
import os
import logging
from pathlib import Path
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_knowledge_base_documents():
    """检查知识库文档数量"""
    print("=== 检查知识库文档数量 ===")
    
    try:
        from vector_store import FaissVectorStore
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        vector_store_path = "knowledge_base/vector_store"
        
        # 检查向量存储文件
        index_file = Path(f"{vector_store_path}.index")
        pkl_file = Path(f"{vector_store_path}.pkl")
        
        print(f"向量存储文件检查:")
        print(f"  索引文件存在: {index_file.exists()}")
        print(f"  数据文件存在: {pkl_file.exists()}")
        
        if index_file.exists() and pkl_file.exists():
            # 加载向量存储
            vector_store.load(vector_store_path)
            
            # 获取文档统计
            stats = vector_store.get_statistics()
            print(f"\n向量存储统计信息:")
            print(f"  总文档数: {stats.get('total_documents', 0)}")
            print(f"  总文本块数: {stats.get('total_chunks', 0)}")
            print(f"  向量维度: {stats.get('vector_dimension', 0)}")
            print(f"  索引大小: {stats.get('index_size', 0)}")
            
            # 检查文档列表
            documents = stats.get('documents', [])
            print(f"\n文档列表 ({len(documents)} 个):")
            for i, doc in enumerate(documents[:10]):  # 只显示前10个
                print(f"  {i+1}. {doc.get('path', 'N/A')} - {doc.get('chunk_count', 0)} 块")
            
            if len(documents) > 10:
                print(f"  ... 还有 {len(documents) - 10} 个文档")
            
            # 检查实际文档内容
            if hasattr(vector_store, 'documents') and vector_store.documents:
                print(f"\n实际文档内容检查:")
                print(f"  向量存储中的文档数量: {len(vector_store.documents)}")
                
                # 统计不同源文件
                sources = {}
                for text, metadata in vector_store.documents:
                    source = metadata.get('source', 'unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print(f"  不同源文件数量: {len(sources)}")
                print(f"  源文件统计:")
                for source, count in list(sources.items())[:10]:
                    print(f"    {source}: {count} 块")
                
                if len(sources) > 10:
                    print(f"    ... 还有 {len(sources) - 10} 个源文件")
            
            return stats
        else:
            print("向量存储文件不存在")
            return None
            
    except Exception as e:
        print(f"检查知识库文档数量失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def check_upload_directories():
    """检查上传目录"""
    print("\n=== 检查上传目录 ===")
    
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        print("上传目录不存在")
        return
    
    total_files = 0
    for type_dir in upload_dir.glob('*'):
        if type_dir.is_dir():
            files = list(type_dir.glob('*'))
            file_count = len([f for f in files if f.is_file()])
            total_files += file_count
            print(f"  {type_dir.name}: {file_count} 个文件")
    
    print(f"上传目录总文件数: {total_files}")

def test_search_consistency():
    """测试搜索一致性"""
    print("\n=== 测试搜索一致性 ===")
    
    try:
        from knowledge_query_service import get_knowledge_query_service
        
        # 获取查询服务
        service = get_knowledge_query_service()
        
        # 测试查询
        test_query = "Russia oil tanker split apart"
        print(f"测试查询: '{test_query}'")
        
        # 微信端搜索
        print("\n微信端搜索:")
        wechat_result = service.search_for_wechat(test_query)
        print(f"  成功: {wechat_result.get('success', False)}")
        print(f"  消息: {wechat_result.get('message', 'N/A')}")
        wechat_results = wechat_result.get('results', [])
        print(f"  结果数量: {len(wechat_results)}")
        
        for i, result in enumerate(wechat_results[:3]):
            print(f"    结果 {i+1}: 分数={result.get('score', 0):.4f}")
            print(f"      内容: {result.get('content', '')[:100]}...")
        
        # Web端搜索
        print("\nWeb端搜索:")
        web_result = service.search_for_web(test_query)
        print(f"  成功: {web_result.get('success', False)}")
        print(f"  消息: {web_result.get('message', 'N/A')}")
        web_results = web_result.get('results', [])
        print(f"  结果数量: {len(web_results)}")
        
        for i, result in enumerate(web_results[:3]):
            print(f"    结果 {i+1}: 分数={result.get('score', 0):.4f}")
            print(f"      内容: {result.get('content', '')[:100]}...")
        
        # 比较结果
        print(f"\n结果比较:")
        print(f"  微信端找到: {len(wechat_results)} 个结果")
        print(f"  Web端找到: {len(web_results)} 个结果")
        
        if len(wechat_results) != len(web_results):
            print(f"  ⚠ 结果数量不一致!")
        else:
            print(f"  ✓ 结果数量一致")
        
        # 检查配置差异
        wechat_config = service.search_config.get_wechat_config()
        web_config = service.search_config.get_web_config()
        print(f"\n配置差异:")
        print(f"  微信端: top_k={wechat_config[0]}, min_score={wechat_config[1]}")
        print(f"  Web端: top_k={web_config[0]}, min_score={web_config[1]}")
        
        return wechat_result, web_result
        
    except Exception as e:
        print(f"测试搜索一致性失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def test_vector_store_direct_search():
    """直接测试向量存储搜索"""
    print("\n=== 直接测试向量存储搜索 ===")
    
    try:
        from vector_store import FaissVectorStore
        
        # 初始化向量存储
        vector_store = FaissVectorStore()
        vector_store_path = "knowledge_base/vector_store"
        
        if Path(f"{vector_store_path}.index").exists():
            vector_store.load(vector_store_path)
            
            # 直接搜索
            test_query = "Russia oil tanker split apart"
            print(f"测试查询: '{test_query}'")
            
            # 使用不同的top_k值测试
            for top_k in [3, 5, 10]:
                print(f"\n使用 top_k={top_k}:")
                results = vector_store.search(test_query, top_k=top_k)
                print(f"  找到 {len(results)} 个结果")
                
                for i, (text, score, metadata) in enumerate(results[:3]):
                    print(f"    结果 {i+1}: 分数={score:.4f}")
                    print(f"      内容: {text[:100]}...")
                    print(f"      源文件: {metadata.get('source', 'N/A')}")
            
            return True
        else:
            print("向量存储文件不存在")
            return False
            
    except Exception as e:
        print(f"直接测试向量存储搜索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_config_files():
    """检查配置文件"""
    print("\n=== 检查配置文件 ===")
    
    config_file = Path("config.conf")
    if config_file.exists():
        print("配置文件存在")
        
        # 读取关键配置
        try:
            from config_loader import config
            
            print("关键配置:")
            print(f"  max_results: {config.getint('vector_store', 'max_results', fallback='N/A')}")
            print(f"  similarity_threshold: {config.getfloat('vector_store', 'similarity_threshold', fallback='N/A')}")
            print(f"  chunk_size: {config.getint('vector_store', 'chunk_size', fallback='N/A')}")
            print(f"  chunk_overlap: {config.getint('vector_store', 'chunk_overlap', fallback='N/A')}")
            
        except Exception as e:
            print(f"读取配置失败: {str(e)}")
    else:
        print("配置文件不存在")

def main():
    """主函数"""
    print("知识库问题诊断工具")
    print("=" * 50)
    
    # 1. 检查知识库文档数量
    stats = check_knowledge_base_documents()
    
    # 2. 检查上传目录
    check_upload_directories()
    
    # 3. 检查配置文件
    check_config_files()
    
    # 4. 测试搜索一致性
    wechat_result, web_result = test_search_consistency()
    
    # 5. 直接测试向量存储搜索
    test_vector_store_direct_search()
    
    # 6. 总结
    print("\n" + "=" * 50)
    print("诊断总结:")
    
    if stats:
        total_docs = stats.get('total_documents', 0)
        total_chunks = stats.get('total_chunks', 0)
        print(f"  知识库文档数量: {total_docs}")
        print(f"  知识库文本块数量: {total_chunks}")
        
        if total_docs != 15:
            print(f"  ⚠ 文档数量不是15，实际为: {total_docs}")
        else:
            print(f"  ✓ 文档数量正确: {total_docs}")
    
    if wechat_result and web_result:
        wechat_count = len(wechat_result.get('results', []))
        web_count = len(web_result.get('results', []))
        
        if wechat_count == 0 and web_count > 0:
            print(f"  ⚠ 微信端查询不到结果，但Web端可以查询到 {web_count} 个结果")
        elif wechat_count > 0 and web_count > 0:
            print(f"  ✓ 两端都能查询到结果")
        elif wechat_count == 0 and web_count == 0:
            print(f"  ⚠ 两端都查询不到结果")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 