import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, UnstructuredPDFLoader
import faiss
import jieba
from sentence_transformers import SentenceTransformer
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from document_manager import DocumentManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaissVectorStore:
    def __init__(self, use_tfidf_fallback: bool = True, dimension: int = 384):
        """
        初始化 FAISS 向量存储
        
        Args:
            use_tfidf_fallback: 是否在加载预训练模型失败时使用 TF-IDF 作为备选
            dimension: 向量维度，默认384维（对TF-IDF模式生效）
        """
        self.texts = []
        self.using_tfidf = False
        self.similarity_threshold = 0.1
        self.dimension = dimension
        
        # 添加自定义词典
        jieba.add_word('退货')
        jieba.add_word('退换货')
        jieba.add_word('换货')
        jieba.add_word('政策')
        jieba.add_word('退款')
        
        # 尝试加载预训练模型
        try:
            logger.info("尝试加载预训练模型...")
            model_name = "shibing624/text2vec-base-chinese"
            cache_dir = os.path.join(os.getcwd(), 'models')
            os.makedirs(cache_dir, exist_ok=True)
            
            self.model = SentenceTransformer(
                model_name,
                cache_folder=cache_dir
            )
            logger.info("预训练模型加载成功")
            self.dimension = self.model.get_sentence_embedding_dimension()
                
        except Exception as e:
            logger.warning(f"加载预训练模型失败，使用TF-IDF作为备选: {str(e)}")
            self.using_tfidf = True
            self.vectorizer = TfidfVectorizer(
                max_features=self.dimension,
                token_pattern=r"(?u)\b\w+\b"
            )
            
        # 初始化FAISS索引
        self.index = faiss.IndexFlatIP(self.dimension)  # 使用内积相似度
        logger.info(f"FAISS索引初始化完成，维度: {self.dimension}")
        
    def preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 输入文本
            
        Returns:
            str: 预处理后的文本
        """
        # 移除多余的空白字符
        text = ' '.join(text.split())
        # 转换为小写
        text = text.lower()
        return text
        
    def add(self, texts: List[str]) -> None:
        """
        添加文本到向量存储
        
        Args:
            texts: 要添加的文本列表
        """
        if not texts:
            return
            
        try:
            # 预处理文本
            processed_texts = [self.preprocess_text(text) for text in texts]
            logger.info(f"预处理后的文本示例: {processed_texts[0][:100]}")
            
            # 生成文本向量
            if self.using_tfidf:
                # 使用jieba分词
                tokenized_texts = []
                for text in processed_texts:
                    words = jieba.cut(text)
                    tokenized_text = " ".join(words)
                    tokenized_texts.append(tokenized_text)
                    logger.info(f"分词结果示例: {tokenized_text[:100]}")
                
                # 如果是第一次添加文本，需要先训练vectorizer
                if not self.texts:
                    self.vectorizer.fit(tokenized_texts)
                    
                vectors = self.vectorizer.transform(tokenized_texts).toarray()
                logger.info(f"TF-IDF向量形状: {vectors.shape}")
                
                # 确保向量维度正确
                if vectors.shape[1] < self.dimension:
                    vectors = np.pad(vectors, ((0, 0), (0, self.dimension - vectors.shape[1])))
                elif vectors.shape[1] > self.dimension:
                    vectors = vectors[:, :self.dimension]
            else:
                # 使用预训练模型生成向量
                vectors = self.model.encode(processed_texts, convert_to_numpy=True)
                logger.info(f"预训练模型向量形状: {vectors.shape}")
                
            # 确保向量是float32类型
            vectors = vectors.astype(np.float32)
            
            # 添加到FAISS索引
            self.index.add(vectors)
            
            # 保存文本
            self.texts.extend(texts)  # 保存原始文本
            logger.info(f"成功添加 {len(texts)} 条文本")
            
        except Exception as e:
            logger.error(f"添加文本失败: {str(e)}")
            raise
            
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        搜索最相似的文本
        
        Args:
            query: 查询文本
            top_k: 返回的最相似文本数量
            
        Returns:
            List[Tuple[str, float]]: 文本和相似度得分的列表
        """
        try:
            if not self.texts:
                return []
                
            # 预处理查询文本
            processed_query = self.preprocess_text(query)
            logger.info(f"预处理后的查询文本: {processed_query}")
            
            if self.using_tfidf:
                # 对查询文本进行分词
                words = jieba.cut(processed_query)
                tokenized_query = " ".join(words)
                logger.info(f"查询文本分词结果: {tokenized_query}")
                
                # 使用TF-IDF向量化查询
                query_vector = self.vectorizer.transform([tokenized_query]).toarray()
                logger.info(f"查询向量形状: {query_vector.shape}")
                
                # 确保向量维度正确
                if query_vector.shape[1] < self.dimension:
                    query_vector = np.pad(query_vector, ((0, 0), (0, self.dimension - query_vector.shape[1])))
                elif query_vector.shape[1] > self.dimension:
                    query_vector = query_vector[:, :self.dimension]
            else:
                # 使用预训练模型生成向量
                query_vector = self.model.encode([processed_query], convert_to_numpy=True)
                logger.info(f"查询向量形状: {query_vector.shape}")
                
            # 确保向量是float32类型
            query_vector = query_vector.astype(np.float32)
            
            # 搜索最相似的向量
            scores, indices = self.index.search(query_vector, min(top_k, len(self.texts)))
            logger.info(f"搜索结果 - 分数: {scores[0]}, 索引: {indices[0]}")
            
            # 过滤并返回结果
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.texts):  # 确保索引有效
                    if score >= self.similarity_threshold:
                        results.append((self.texts[idx], float(score)))
                        logger.info(f"匹配文本 (得分: {score:.4f}): {self.texts[idx][:100]}...")
                    
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise
            
    def save(self, path: str) -> None:
        """
        保存向量存储到文件
        
        Args:
            path: 保存路径
        """
        try:
            # 创建保存目录
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 保存FAISS索引
            faiss.write_index(self.index, f"{path}.index")
            
            # 保存其他数据
            data = {
                "texts": self.texts,
                "using_tfidf": self.using_tfidf,
                "dimension": self.dimension,
                "similarity_threshold": self.similarity_threshold
            }
            
            # 如果使用TF-IDF，还需要保存vectorizer
            if self.using_tfidf:
                data["vectorizer"] = self.vectorizer
                
            with open(f"{path}.pkl", "wb") as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"保存失败: {str(e)}")
            raise
            
    def load(self, path: str) -> None:
        """
        从文件加载向量存储
        
        Args:
            path: 加载路径
        """
        try:
            # 加载FAISS索引
            self.index = faiss.read_index(f"{path}.index")
            
            # 加载其他数据
            with open(f"{path}.pkl", "rb") as f:
                data = pickle.load(f)
                
            self.texts = data["texts"]
            self.using_tfidf = data["using_tfidf"]
            self.dimension = data["dimension"]
            self.similarity_threshold = data.get("similarity_threshold", 0.1)
            
            # 如果使用TF-IDF，还需要加载vectorizer
            if self.using_tfidf:
                self.vectorizer = data["vectorizer"]
                
            logger.info(f"成功加载向量存储，包含 {len(self.texts)} 条文本")
            
        except Exception as e:
            logger.error(f"加载失败: {str(e)}")
            raise

class SmartKnowledgeBase:
    def __init__(self, vector_store_path: str = "data/vector_store"):
        """
        初始化知识库
        
        Args:
            vector_store_path: 向量存储路径
        """
        self.vector_store_path = vector_store_path
        self.document_manager = DocumentManager()
        
        # 确保向量存储目录存在
        os.makedirs(vector_store_path, exist_ok=True)
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
        )
        
        # 初始化向量存储
        if os.path.exists(os.path.join(vector_store_path, "index.faiss")):
            self.vector_store = FaissVectorStore()
            self.vector_store.load(vector_store_path)
        else:
            self.vector_store = FaissVectorStore()
            self.vector_store.add(["初始化向量库"])
            self.vector_store.save(vector_store_path)
        
    def add_texts(self, texts: List[str]) -> bool:
        """
        添加文本到知识库
        """
        try:
            # 添加到向量存储
            self.vector_store.add(texts)
            # 保存向量存储
            self.vector_store.save(self.vector_store_path)
            return True
        except Exception as e:
            print(f"添加文本失败: {e}")
            return False
            
    def add_document(self, file_path: str) -> bool:
        """
        添加文档到知识库
        
        Args:
            file_path: 文档路径
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 根据文件类型选择加载器
            file_path = Path(file_path)
            if file_path.suffix.lower() == '.pdf':
                loader = UnstructuredPDFLoader(str(file_path))
            else:
                loader = TextLoader(str(file_path), encoding='utf-8')
                
            # 加载文档
            documents = loader.load()
            
            # 分割文本
            texts = self.text_splitter.split_documents(documents)
            
            # 获取文本内容
            text_contents = [doc.page_content for doc in texts]
            
            # 添加到向量存储
            if self.add_texts(text_contents):
                # 添加到文档管理器
                return self.document_manager.add_document(str(file_path), len(texts))
            return False
            
        except Exception as e:
            print(f"添加文档失败: {e}")
            return False
            
    def remove_document(self, file_path: str) -> bool:
        """
        从知识库中删除文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 从文档管理器中删除
            if not self.document_manager.remove_document(file_path):
                return False
            
            # 从向量存储中删除
            if hasattr(self.vector_store, 'documents'):
                # 找到所有属于该文档的文本块
                file_path = str(Path(file_path))
                new_documents = []
                new_embeddings = []
                
                # 遍历所有文本块，保留不属于被删除文档的块
                for i, (text, metadata) in enumerate(self.vector_store.documents):
                    if metadata.get('source') != file_path:
                        new_documents.append((text, metadata))
                        if self.vector_store.document_embeddings is not None:
                            new_embeddings.append(self.vector_store.document_embeddings[i])
                
                # 更新文档列表和向量
                self.vector_store.documents = new_documents
                if new_embeddings:
                    self.vector_store.document_embeddings = np.array(new_embeddings)
                    
                    # 重建索引
                    self.vector_store.index.reset()
                    if len(new_embeddings) > 0:
                        self.vector_store.index.add(self.vector_store.document_embeddings)
                
                # 保存更新后的向量存储
                self.vector_store.save(self.vector_store_path)
                
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
            
    def get_statistics(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            # 获取文档管理器的统计信息
            total_documents = self.document_manager.get_total_documents()
            total_chunks = self.document_manager.get_total_chunks()
            documents = self.document_manager.get_all_documents()
            
            # 获取向量维度
            vector_dimension = 0
            if hasattr(self.vector_store, 'dimension'):
                vector_dimension = self.vector_store.dimension
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "documents": documents,
                "vector_dimension": vector_dimension
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "documents": [],
                "vector_dimension": 0
            }
            
    def query(self, question: str, top_k: int = 3) -> str:
        """
        查询知识库
        
        Args:
            question: 问题
            top_k: 返回的相关文档数量
            
        Returns:
            str: 答案
        """
        try:
            # 搜索相关文档
            print(f"\n=== 开始查询知识库 ===")
            print(f"问题: {question}")
            print(f"当前相似度阈值: {self.vector_store.similarity_threshold}")
            
            # 调整相似度阈值为更小的值
            original_threshold = self.vector_store.similarity_threshold
            self.vector_store.similarity_threshold = 0.01  # 设置一个较小的阈值
            
            results = self.vector_store.search(question, top_k=top_k)
            print(f"\n找到 {len(results)} 个结果:")
            
            # 提取相关内容
            relevant_docs = []
            for text, score in results:
                print(f"\n相似度得分: {score:.4f}")
                print(f"文本内容: {text[:200]}...")
                if score > self.vector_store.similarity_threshold:
                    relevant_docs.append(text)
                    
            if not relevant_docs:
                print("\n没有找到相关内容")
                return None
                
            # 合并相关内容
            context = "\n".join(relevant_docs)
            print(f"\n最终返回内容长度: {len(context)} 字符")
            
            # 恢复原始阈值
            self.vector_store.similarity_threshold = original_threshold
            
            return context
            
        except Exception as e:
            print(f"查询出错: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def save(self):
        """保存知识库"""
        try:
            self.vector_store.save(self.vector_store_path)
            print("知识库保存成功")
        except Exception as e:
            print(f"保存知识库失败: {e}")
            
    def load(self):
        """加载知识库"""
        try:
            self.vector_store.load(self.vector_store_path)
            print("知识库加载成功")
        except Exception as e:
            print(f"加载知识库失败: {e}")
            
# 测试代码
if __name__ == "__main__":
    kb = SmartKnowledgeBase()
    # 添加文档
    kb.add_document("test.txt")
    # 查询
    result = kb.query("测试问题") 