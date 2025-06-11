from vector_store import VectorStore
from loguru import logger
import json
import traceback
from pathlib import Path

def test_knowledge_base():
    """测试知识库的文档检索功能"""
    try:
        # 初始化向量存储
        logger.info("初始化向量存储...")
        vector_store = VectorStore()
        
        # 加载现有的向量存储
        vector_store_path = Path("knowledge_base/vector_store")
        if vector_store_path.with_suffix('.json').exists():
            logger.info("加载现有向量存储...")
            vector_store.load(str(vector_store_path))
            
            # 显示当前文档数量
            logger.info(f"当前包含 {len(vector_store.documents)} 个文档")
            
            # 显示文档示例
            if vector_store.documents:
                logger.info("\n文档示例:")
                for i, doc in enumerate(vector_store.documents[:3]):  # 只显示前3个
                    logger.info(f"文档 {i+1}:")
                    logger.info(f"- 内容: {doc.content}")
                    logger.info(f"- 元数据: {doc.metadata}")
            
            # 测试搜索功能
            test_queries = [
                "智能手机",
                "笔记本电脑",
                "平板电脑",
                "智能手表",
                "处理器",
                "屏幕"
            ]
            
            logger.info("\n开始测试搜索功能...")
            for query in test_queries:
                logger.info(f"\n搜索查询: {query}")
                results = vector_store.search(query, top_k=3)
                
                if results:
                    logger.info(f"找到 {len(results)} 个相关结果:")
                    for i, result in enumerate(results, 1):
                        logger.info(f"结果 {i}:")
                        logger.info(f"- 内容: {result['content']}")
                        logger.info(f"- 相似度: {result['score']:.4f}")
                        logger.info(f"- 元数据: {result['metadata']}")
                else:
                    logger.warning(f"没有找到与 '{query}' 相关的结果")
        else:
            logger.warning("未找到向量存储文件")
            
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_knowledge_base() 