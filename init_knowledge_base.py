import os
import shutil
from pathlib import Path
from smart_kb import SmartKnowledgeBase
from vector_store import FaissVectorStore

def init_knowledge_base():
    """Initialize the knowledge base with offline capabilities"""
    print("\n=== 初始化知识库 ===")
    
    # 清理现有的知识库文件
    kb_dir = Path("knowledge_base")
    if kb_dir.exists():
        print("清理现有知识库...")
        try:
            # 删除vector_store相关文件
            for file in kb_dir.glob("vector_store*"):
                if file.is_file():
                    file.unlink()
                    print(f"已删除 {file}")
                elif file.is_dir():
                    shutil.rmtree(file)
                    print(f"已删除目录 {file}")
        except Exception as e:
            print(f"清理文件时出错: {str(e)}")
            return False
    
    try:
        # 创建新的知识库实例
        print("\n创建新的知识库实例...")
        kb = SmartKnowledgeBase()
        
        # 添加测试文档
        print("\n添加测试文档...")
        test_text = """
        欢迎使用知识库系统

        这是一个测试文档，包含以下内容：

        1. 退换货政策
        我们的退换货政策非常简单：
        - 收到商品后15天内可以申请退换
        - 商品必须保持原包装完整
        - 退货运费由买家承担

        2. 运费说明
        - 单笔订单满99元包邮
        - 偏远地区需额外支付运费
        - 特大件商品另计运费

        3. 联系方式
        - 客服电话：400-123-4567
        - 工作时间：周一至周日 9:00-18:00
        - 电子邮箱：support@example.com
        """
        
        success = kb.add_texts([test_text])
        if success:
            print("测试文档添加成功")
        else:
            print("测试文档添加失败")
        
        print("\n知识库初始化成功!")
        return True
        
    except Exception as e:
        print(f"\n初始化知识库时出错: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_knowledge_base()
    print(f"\n初始化{'成功' if success else '失败'}") 