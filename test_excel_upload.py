import os
from pathlib import Path
import pandas as pd
from smart_kb import SmartKnowledgeBase
from document_processor import DocumentProcessor
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_excel_processing():
    """测试Excel文件处理和知识库集成"""
    
    # 创建测试Excel文件
    test_data = {
        '姓名': ['张三', '李四', '王五'],
        '年龄': [25, 30, 35],
        '职位': ['工程师', '设计师', '产品经理']
    }
    df = pd.DataFrame(test_data)
    
    # 保存测试文件
    test_file = 'test_data.xlsx'
    df.to_excel(test_file, index=False)
    logger.info(f"创建测试Excel文件: {test_file}")
    
    try:
        # 初始化文档处理器
        doc_processor = DocumentProcessor()
        logger.info("初始化文档处理器")
        
        # 处理Excel文件
        logger.info(f"开始处理Excel文件: {test_file}")
        chunks = doc_processor.process_file(test_file)
        logger.info(f"生成了 {len(chunks)} 个文本块")
        
        # 初始化知识库
        kb = SmartKnowledgeBase()
        logger.info("初始化知识库")
        
        # 添加文档到知识库
        texts = [chunk.content for chunk in chunks]
        metadata = [chunk.metadata for chunk in chunks]
        success = kb.add_texts(texts, metadata)
        logger.info(f"添加到知识库: {'成功' if success else '失败'}")
        
        # 测试检索
        test_query = "工程师"
        logger.info(f"测试检索: {test_query}")
        results = kb.query(test_query)
        
        if results:
            logger.info("检索结果:")
            for i, result in enumerate(results, 1):
                logger.info(f"结果 {i}:")
                logger.info(f"- 内容: {result['content']}")
                logger.info(f"- 相似度: {result['score']}")
                logger.info(f"- 元数据: {result['metadata']}")
        else:
            logger.warning("没有找到相关结果")
            
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        raise
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info(f"清理测试文件: {test_file}")

if __name__ == "__main__":
    test_excel_processing() 