from typing import List
import os
import torch
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import jieba
import traceback

class SmartEmbeddings(Embeddings):
    """智能文本嵌入实现，支持多种后备方案"""
    
    def __init__(self):
        print("初始化智能向量化方法...")
        self.model = None
        self.fallback = None
        self.initialize_embeddings()
        
    def initialize_embeddings(self):
        """初始化嵌入模型，包含多个备选方案"""
        # 设置模型缓存目录
        cache_dir = os.path.join(os.getcwd(), 'models')
        os.makedirs(cache_dir, exist_ok=True)
        
        # 模型加载顺序：本地缓存 -> 下载 -> TF-IDF备选
        model_candidates = [
            ('shibing624/text2vec-base-chinese', '中文模型'),
            ('sentence-transformers/all-MiniLM-L6-v2', '通用模型'),
            ('sentence-transformers/paraphrase-MiniLM-L3-v2', '轻量模型')
        ]
        
        for model_name, model_type in model_candidates:
            try:
                print(f"尝试加载{model_type} {model_name}...")
                self.model = SentenceTransformer(
                    model_name,
                    device='cpu' if not torch.cuda.is_available() else 'cuda',
                    cache_folder=cache_dir,
                    trust_remote_code=True
                )
                print(f"成功加载{model_type}")
                return
            except Exception as e:
                print(f"加载{model_type}失败: {str(e)}")
                continue
        
        # 如果所有模型都加载失败，使用TF-IDF作为备选方案
        print("所有模型加载失败，使用TF-IDF作为备选方案")
        self.fallback = TfidfEmbeddings()
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """生成文档嵌入向量"""
        try:
            if self.model is not None:
                embeddings = self.model.encode(texts, convert_to_tensor=False)
                return embeddings.tolist()
            else:
                return self.fallback.embed_documents(texts)
        except Exception as e:
            print(f"生成文档向量时出错: {e}")
            if self.fallback is None:
                self.fallback = TfidfEmbeddings()
            return self.fallback.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """生成查询文本的嵌入向量"""
        return self.embed_documents([text])[0]

class TfidfEmbeddings(Embeddings):
    """使用TF-IDF的文本嵌入实现（离线备选方案）"""
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.vectorizer = TfidfVectorizer(
            max_features=dimension,
            token_pattern=r"(?u)\b\w+\b"
        )
        self.fitted = False
        
    def fit(self, texts: List[str]):
        """训练TF-IDF向量化器"""
        # 对中文文本进行分词
        processed_texts = []
        for text in texts:
            words = jieba.cut(text)
            processed_text = " ".join(words)
            processed_texts.append(processed_text)
            
        self.vectorizer.fit(processed_texts)
        self.fitted = True
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """生成文档嵌入向量"""
        if not self.fitted:
            self.fit(texts)
            
        # 处理输入文本
        processed_texts = []
        for text in texts:
            words = jieba.cut(text)
            processed_text = " ".join(words)
            processed_texts.append(processed_text)
            
        # 生成TF-IDF向量
        vectors = self.vectorizer.transform(processed_texts).toarray()
        
        # 填充或截断到指定维度
        padded_vectors = []
        for vector in vectors:
            if len(vector) < self.dimension:
                padded_vector = np.pad(vector, (0, self.dimension - len(vector)))
            else:
                padded_vector = vector[:self.dimension]
            padded_vectors.append(padded_vector.tolist())
            
        return padded_vectors
    
    def embed_query(self, text: str) -> List[float]:
        """生成查询文本的嵌入向量"""
        return self.embed_documents([text])[0] 