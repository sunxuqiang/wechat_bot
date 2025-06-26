import os
import logging
import numpy as np
import faiss
from typing import List, Tuple, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import torch
import traceback
from pathlib import Path
import pickle
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
import time
import requests
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential
import functools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def network_error_handler(func):
    """网络错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_delay = 1
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except (RequestException, ConnectionError) as e:
                retries += 1
                if retries == max_retries:
                    logger.error(f"网络错误，已达到最大重试次数: {str(e)}")
                    raise
                wait_time = retry_delay * (2 ** (retries - 1))  # 指数退避
                logger.warning(f"网络错误，{wait_time}秒后进行第{retries}次重试: {str(e)}")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"未知错误: {str(e)}")
                raise
        return None
    return wrapper

class FaissVectorStore:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            logger.info("初始化向量存储...")
            self.documents = []
            self.document_embeddings = None
            self.index = None
            self.model = None
            self.similarity_threshold = 0.3  # 调高基础相似度阈值到0.3
            self.max_retries = 3  # 最大重试次数
            self.retry_delay = 1  # 初始重试延迟（秒）
            self.initialize_model()
            # 初始化TF-IDF计算器
            self.tfidf_vectorizer = TfidfVectorizer(
                tokenizer=lambda x: jieba.lcut_for_search(x),
                token_pattern=None,
                min_df=2,  # 至少出现在2个文档中
                max_df=0.8  # 最多出现在80%的文档中
            )
            self.keyword_importance = {}  # 存储关键词重要性
            FaissVectorStore._initialized = True
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def initialize_model(self):
        """初始化向量模型"""
        try:
            # 使用本地缓存
            cache_dir = os.path.join(os.path.dirname(__file__), 'models', 'text2vec-base-chinese')
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"模型目录: {cache_dir}")
            
            # 使用text2vec-base-chinese模型
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"使用设备: {device}")
            
            logger.info("正在初始化模型...")
            self.model = SentenceTransformer(cache_dir)
            self.model.to(device)
            
            # 初始化FAISS索引为L2距离
            dim = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(dim)  # 使用L2距离
            logger.info(f"FAISS 索引初始化成功，维度: {dim}")
            
        except Exception as e:
            logger.error(f"初始化向量模型失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def validate_vectors(self, vectors: np.ndarray, name: str = "vectors") -> bool:
        """验证向量的质量
        
        Args:
            vectors: 要验证的向量
            name: 向量名称，用于日志
            
        Returns:
            bool: 向量是否有效
        """
        try:
            # 检查是否有NaN或inf
            if np.any(np.isnan(vectors)) or np.any(np.isinf(vectors)):
                logger.error(f"{name} 包含 NaN 或 inf 值")
                return False
                
            # 检查向量范数
            norms = np.linalg.norm(vectors, axis=1)
            logger.debug(f"{name} 范数统计:")
            logger.debug(f"- 最小值: {norms.min():.4f}")
            logger.debug(f"- 最大值: {norms.max():.4f}")
            logger.debug(f"- 平均值: {norms.mean():.4f}")
            logger.debug(f"- 标准差: {norms.std():.4f}")
            
            # 对于归一化后的向量，范数应该接近1
            if abs(norms.mean() - 1.0) > 0.1:
                logger.warning(f"{name} 的平均范数 ({norms.mean():.4f}) 与预期值 1.0 相差较大")
                
            return True
            
        except Exception as e:
            logger.error(f"验证向量失败: {str(e)}")
            return False

    def normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """标准化向量"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def calculate_keyword_match(self, query: str, text: str) -> float:
        """计算关键词匹配度"""
        # 分词并过滤停用词
        query_words = set(w for w in jieba.lcut_for_search(query) if len(w) > 1)
        text_words = set(w for w in jieba.lcut_for_search(text) if len(w) > 1)
        
        if not query_words or not text_words:
            return 0.0
            
        # 计算关键词匹配数量
        matches = query_words & text_words
        if not matches:
            return 0.0
            
        # 计算匹配率
        match_ratio = len(matches) / len(query_words)
        return match_ratio

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        # 标准化向量
        vec1_normalized = self.normalize_vector(vec1)
        vec2_normalized = self.normalize_vector(vec2)
        
        # 计算余弦相似度
        similarity = float(np.dot(vec1_normalized, vec2_normalized))
        
        # 确保相似度在[0,1]范围内
        return max(0.0, min(1.0, similarity))

    def calculate_keyword_overlap(self, query: str, text: str) -> float:
        """计算关键词重叠度"""
        query_words = set(w for w in jieba.lcut_for_search(query) if len(w) > 1)
        text_words = set(w for w in jieba.lcut_for_search(text) if len(w) > 1)
        
        if not query_words or not text_words:
            return 0.0
            
        intersection = query_words & text_words
        if not intersection:
            return 0.0
            
        return len(intersection) / len(query_words)

    def calculate_keyword_importance(self, query: str, text: str) -> float:
        """计算查询关键词在文档中的重要性得分"""
        # 分词并过滤
        query_words = [w for w in jieba.lcut_for_search(query) if len(w) > 1]
        if not query_words:
            return 0.0
            
        # 计算词频
        word_freq = {}
        text_words = jieba.lcut(text)
        for word in text_words:
            word_freq[word] = word_freq.get(word, 0) + 1
            
        # 检查关键词匹配
        matched_words = set(query_words) & set(text_words)
        if not matched_words:
            return 0.0
            
        # 计算匹配率
        match_rate = len(matched_words) / len(query_words)
        if match_rate < 0.3:  # 调高匹配率阈值到30%
            return 0.0
            
        # 计算位置得分
        position_scores = []
        text_len = len(text)
        for word in matched_words:
            positions = []
            start = 0
            while True:
                pos = text.find(word, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
                
            if positions:
                position_score = sum(1 - (pos / text_len) for pos in positions) / len(positions)
                position_scores.append(position_score)
                
        if not position_scores:
            return 0.0
            
        # 结合词频和位置信息
        importance = sum(
            word_freq.get(word, 0) * self.keyword_importance.get(word, 1.0)
            for word in matched_words
        ) / len(matched_words)
        
        # 综合考虑词频、位置和匹配率
        return (importance * 0.4 + sum(position_scores) * 0.3 + match_rate * 0.3)

    def calculate_semantic_similarity(self, query: str, text: str) -> float:
        """计算语义相关度
        
        使用更细粒度的语义分析来评估查询和文本的相关性
        """
        # 将长文本分成句子
        text_sentences = [s.strip() for s in text.split('。') if s.strip()]
        if not text_sentences:
            return 0.0
            
        # 对每个句子计算与查询的相似度
        sentence_scores = []
        query_vector = self.model.encode([query], convert_to_tensor=True)[0]
        
        for sentence in text_sentences[:3]:  # 只取前3个句子，避免计算过多
            try:
                sentence_vector = self.model.encode([sentence], convert_to_tensor=True)[0]
                similarity = self.cosine_similarity(query_vector.cpu().numpy(), sentence_vector.cpu().numpy())
                sentence_scores.append(similarity)
            except Exception as e:
                logger.warning(f"计算句子相似度失败: {str(e)}")
                continue
                
        # 如果没有有效的句子相似度，返回0
        if not sentence_scores:
            return 0.0
            
        # 返回最高的句子相似度
        return max(sentence_scores)

    def calculate_semantic_coherence(self, query: str, text: str) -> float:
        """计算语义连贯性"""
        # 将文本分成句子
        sentences = [s.strip() for s in text.split('。') if s.strip()]
        if not sentences:
            return 0.0
            
        # 对查询和每个句子进行向量化
        query_vector = self.model.encode([query], convert_to_tensor=True)[0]
        sentence_vectors = self.model.encode(sentences[:3], convert_to_tensor=True)
        
        # 计算句子间的语义连贯性
        coherence_scores = []
        query_similarities = []
        prev_vector = None
        
        for i, sent_vector in enumerate(sentence_vectors):
            # 计算与查询的相似度
            query_sim = float(self.cosine_similarity(query_vector.cpu().numpy(), sent_vector.cpu().numpy()))
            query_similarities.append(query_sim)
            
            # 计算与前一个句子的连贯性
            if prev_vector is not None:
                coherence = float(self.cosine_similarity(prev_vector.cpu().numpy(), sent_vector.cpu().numpy()))
                coherence_scores.append(coherence)
                
            prev_vector = sent_vector
            
        # 如果只有一个句子，检查与查询的相似度
        if not coherence_scores:
            avg_query_sim = sum(query_similarities) / len(query_similarities)
            return avg_query_sim if avg_query_sim > 0.5 else 0.0
            
        # 计算平均查询相似度和连贯性
        avg_query_sim = sum(query_similarities) / len(query_similarities)
        avg_coherence = sum(coherence_scores) / len(coherence_scores)
        
        # 如果平均查询相似度过低，返回0
        if avg_query_sim < 0.4:
            return 0.0
            
        # 综合考虑查询相似度和语义连贯性
        return 0.7 * avg_query_sim + 0.3 * avg_coherence

    def is_query_valid(self, query: str) -> bool:
        """检查查询是否有效"""
        # 去除空白字符
        query = query.strip()
        
        # 检查长度
        if len(query) < 2:
            logger.warning("查询内容过短")
            return False
            
        # 分词检查
        words = [w for w in jieba.lcut_for_search(query) if len(w) > 1]
        if not words:
            logger.warning("查询中没有有效关键词")
            return False
            
        return True

    @network_error_handler
    def encode_text(self, text: str) -> np.ndarray:
        """对单个文本进行编码，带有错误处理"""
        try:
            if not text or not text.strip():
                raise ValueError("文本为空")
            return self.model.encode([text.strip()], convert_to_tensor=True)[0].cpu().numpy()
        except Exception as e:
            logger.error(f"文本编码失败: {str(e)}")
            raise

    def add(self, texts: List[str], metadata: Optional[List[Dict]] = None) -> bool:
        """添加文档到向量存储"""
        try:
            if not texts:
                logger.warning("没有文本需要添加")
                return False
                
            # 过滤空文本
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                logger.warning("所有文本都为空，跳过添加")
                return False
                
            logger.info(f"开始处理 {len(valid_texts)} 个有效文本")
            
            # 生成向量嵌入
            logger.info("生成文档向量...")
            try:
                # 使用模型批量编码文本
                embeddings = self.model.encode(valid_texts, convert_to_tensor=True).cpu().numpy()
                logger.info(f"生成了 {len(embeddings)} 个向量")
                
            except Exception as e:
                logger.error(f"生成向量失败: {str(e)}")
                logger.error(traceback.format_exc())
                return False
            
            # 添加到文档存储
            try:
                if self.document_embeddings is None:
                    self.document_embeddings = embeddings
                else:
                    self.document_embeddings = np.vstack([self.document_embeddings, embeddings])
                    
                # 保存文档和元数据
                if metadata is None:
                    metadata = [{}] * len(valid_texts)
                elif len(metadata) != len(valid_texts):
                    # 如果元数据长度不匹配，调整元数据
                    if len(metadata) > len(valid_texts):
                        metadata = metadata[:len(valid_texts)]
                    else:
                        metadata.extend([{}] * (len(valid_texts) - len(metadata)))
                        
                self.documents.extend(list(zip(valid_texts, metadata)))
                logger.info(f"文档已保存，当前总数: {len(self.documents)}")
                
                return True
                
            except Exception as e:
                logger.error(f"保存文档失败: {str(e)}")
                logger.error(traceback.format_exc())
                return False
            
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
    def distance_to_similarity(self, distance: float) -> float:
        """将L2距离转换为相似度分数
        
        Args:
            distance: L2距离值
            
        Returns:
            float: 相似度分数 (0-1范围)
        """
        # 使用修改后的高斯核，调整sigma参数使得相似度分数分布更合理
        # 增大sigma值会使得相似度分数的分布更加平缓
        sigma = 4.0  # 增大sigma值，使得相似度分数更容易超过阈值
        similarity = np.exp(-distance / (2.0 * sigma * sigma))
        return float(similarity)

    def get_adaptive_threshold(self, scores: List[float]) -> float:
        """计算自适应阈值"""
        if not scores:
            return self.similarity_threshold
            
        # 移除零分
        non_zero_scores = [s for s in scores if s > 0]
        if not non_zero_scores:
            return self.similarity_threshold
            
        # 计算分数统计信息
        mean_score = np.mean(non_zero_scores)
        std_score = np.std(non_zero_scores) if len(non_zero_scores) > 1 else 0
        
        # 使用更严格的阈值计算方式
        threshold = max(
            self.similarity_threshold,  # 基础阈值
            mean_score - 0.5 * std_score,  # 统计阈值
            0.4  # 最小阈值
        )
        
        return threshold

    def update_keyword_importance(self, query: str, relevant_docs: List[str]):
        """更新关键词重要性权重"""
        # 提取查询关键词
        query_words = set(w for w in jieba.lcut_for_search(query) if len(w) > 1)
        if not query_words:
            return
            
        # 构建文档集合
        all_docs = [query] + relevant_docs
        
        # 训练TF-IDF
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_docs)
            
            # 获取特征名称（兼容不同版本的scikit-learn）
            try:
                feature_names = self.tfidf_vectorizer.get_feature_names_out()
            except AttributeError:
                try:
                    feature_names = self.tfidf_vectorizer.get_feature_names()
                except AttributeError:
                    logger.error("无法获取TF-IDF特征名称，可能是scikit-learn版本不兼容")
                    return
            
            # 更新关键词重要性
            for word in query_words:
                if word in feature_names:
                    idx = list(feature_names).index(word)
                    # 获取该词在所有文档中的TF-IDF值
                    importance = np.mean(tfidf_matrix[:, idx].toarray())
                    # 更新重要性，使用指数移动平均
                    self.keyword_importance[word] = (
                        0.7 * self.keyword_importance.get(word, importance) +
                        0.3 * importance
                    )
        except Exception as e:
            logger.warning(f"更新关键词重要性失败: {str(e)}")

    def calculate_relevance_score(self, query_vector: np.ndarray, doc_vector: np.ndarray,
                                query: str, text: str) -> Tuple[float, Dict[str, float]]:
        """计算综合相关性得分"""
        # 计算各个维度的相似度
        vector_similarity = float(self.cosine_similarity(query_vector, doc_vector))
        keyword_importance = self.calculate_keyword_importance(query, text)
        semantic_coherence = self.calculate_semantic_coherence(query, text)
        
        # 严格的过滤规则
        if keyword_importance == 0.0:  # 如果关键词重要性为0，说明没有足够的关键词匹配
            return 0.0, {
                'vector_similarity': vector_similarity,
                'keyword_importance': 0.0,
                'semantic_coherence': semantic_coherence
            }
            
        if vector_similarity < 0.3:  # 调高向量相似度阈值到0.3
            return 0.0, {
                'vector_similarity': vector_similarity,
                'keyword_importance': keyword_importance,
                'semantic_coherence': semantic_coherence
            }
            
        if semantic_coherence < 0.3:  # 调高语义连贯性阈值到0.3
            return 0.0, {
                'vector_similarity': vector_similarity,
                'keyword_importance': keyword_importance,
                'semantic_coherence': semantic_coherence
            }
        
        # 动态调整权重
        if keyword_importance > 0.6:  # 提高关键词匹配阈值
            weights = {'vector': 0.3, 'keyword': 0.5, 'coherence': 0.2}
        elif semantic_coherence > 0.8:  # 提高语义连贯性阈值
            weights = {'vector': 0.4, 'keyword': 0.2, 'coherence': 0.4}
        else:
            weights = {'vector': 0.4, 'keyword': 0.3, 'coherence': 0.3}
            
        # 计算综合得分
        scores = {
            'vector_similarity': vector_similarity,
            'keyword_importance': keyword_importance,
            'semantic_coherence': semantic_coherence
        }
        
        # 计算加权得分
        combined_score = (
            weights['vector'] * vector_similarity +
            weights['keyword'] * keyword_importance +
            weights['coherence'] * semantic_coherence
        )
        
        # 最终的相关性检查
        if combined_score < 0.4:  # 调高最终分数阈值到0.4
            return 0.0, scores
            
        return combined_score, scores

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """搜索相似文档"""
        try:
            if not self.is_query_valid(query):
                logger.warning("查询内容无效")
                return []
                
            if not self.documents:
                logger.warning("知识库为空")
                return []
                
            if len(query) < 2:
                logger.warning("查询内容过短")
                return []
                
            logger.info(f"\n{'='*50}")
            logger.info(f"开始搜索: {query}")
            logger.info(f"当前知识库文档数量: {len(self.documents)}")
            logger.info(f"{'='*50}\n")
            
            # 生成查询向量
            try:
                query_vector = self.encode_text(query)
                # 标准化查询向量
                query_vector = self.normalize_vector(query_vector)
            except Exception as e:
                logger.error(f"查询向量生成失败: {str(e)}")
                return []
            
            # 计算与所有文档的相似度
            results = []
            
            for i, (text, metadata) in enumerate(self.documents):
                try:
                    if self.document_embeddings is not None and i < len(self.document_embeddings):
                        # 获取文档向量并标准化
                        doc_vector = self.document_embeddings[i]
                        doc_vector = self.normalize_vector(doc_vector)
                        
                        # 计算向量相似度
                        vector_similarity = self.cosine_similarity(query_vector, doc_vector)
                        
                        # 计算关键词匹配度
                        keyword_match = self.calculate_keyword_match(query, text)
                        
                        # 使用严格的过滤规则
                        if keyword_match == 0:  # 如果没有关键词匹配，直接跳过
                            continue
                            
                        # 计算加权分数
                        # 向量相似度权重降低，关键词匹配权重提高
                        weighted_score = 0.4 * vector_similarity + 0.6 * keyword_match
                        
                        # 恢复原有严格阈值
                        if (vector_similarity >= self.similarity_threshold and 
                            keyword_match >= 0.3 and  # 关键词匹配阈值30%
                            weighted_score >= 0.4):  # 最终分数阈值0.4
                            
                            results.append((
                                text, 
                                weighted_score,
                                {
                                    **metadata,
                                    '_debug_info': {
                                        'vector_similarity': f"{vector_similarity:.4f}",
                                        'keyword_match': f"{keyword_match:.4f}",
                                        'weighted_score': f"{weighted_score:.4f}"
                                    }
                                }
                            ))
                            
                except Exception as e:
                    logger.error(f"处理文档 {i} 时发生错误: {str(e)}")
                    continue
            
            if not results:
                logger.info("未找到相关文档")
                return []
            
            # 按相似度排序
            results.sort(key=lambda x: x[1], reverse=True)
            
            # 输出搜索结果详情
            logger.info("\n搜索结果详情:")
            logger.info(f"{'='*150}")
            logger.info(f"{'序号':^6} | {'加权分数':^10} | {'向量相似度':^12} | {'关键词匹配':^10} | {'文本预览':<90}")
            logger.info(f"{'-'*150}")
            
            for i, (text, score, metadata) in enumerate(results[:top_k]):
                debug_info = metadata.get('_debug_info', {})
                preview = text[:90] + "..." if len(text) > 90 else text
                logger.info(
                    f"{i+1:^6} | {score:^10.4f} | "
                    f"{debug_info.get('vector_similarity', 'N/A'):^12} | "
                    f"{debug_info.get('keyword_match', 'N/A'):^10} | "
                    f"{preview:<90}"
                )
            
            logger.info(f"{'='*150}")
            logger.info(f"找到 {len(results)} 条匹配结果\n")
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    def save(self, path: str) -> None:
        """保存向量存储到文件"""
        try:
            save_dir = Path(path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存索引
            index_path = str(Path(path).with_suffix('.index'))
            faiss.write_index(self.index, index_path)
            logger.info(f"索引已保存到: {index_path}")
            
            # 保存文档和元数据
            data = {
                'documents': self.documents,
                'document_embeddings': self.document_embeddings
            }
            data_path = str(Path(path).with_suffix('.pkl'))
            with open(data_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"数据已保存到: {data_path}")
            
        except Exception as e:
            logger.error(f"保存向量存储失败: {str(e)}")
            logger.error(traceback.format_exc())
            
    def load(self, path: str) -> None:
        """从文件加载向量存储"""
        try:
            # 加载索引
            index_path = str(Path(path).with_suffix('.index'))
            if os.path.exists(index_path):
                try:
                    self.index = faiss.read_index(index_path)
                    logger.info(f"索引已加载: {index_path}")
                except Exception as e:
                    logger.warning(f"索引文件损坏或维度不匹配，重新创建索引: {e}")
                    # 重新创建索引
                    dim = self.model.get_sentence_embedding_dimension()
                    self.index = faiss.IndexFlatL2(dim)
            else:
                logger.warning(f"索引文件不存在: {index_path}")
                return
            
            # 加载文档和元数据
            data_path = str(Path(path).with_suffix('.pkl'))
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                
                # 兼容旧的文件格式
                if 'documents' in data and 'document_embeddings' in data:
                    # 新格式
                    self.documents = data['documents']
                    self.document_embeddings = data['document_embeddings']
                    logger.info(f"使用新格式加载数据: {data_path}")
                elif 'texts' in data and 'metadata' in data:
                    # 旧格式，转换为新格式
                    texts = data['texts']
                    metadata_list = data['metadata']
                    
                    # 重新生成文档向量
                    self.documents = []
                    self.document_embeddings = []
                    
                    for i, (text, metadata) in enumerate(zip(texts, metadata_list)):
                        try:
                            # 生成文本向量
                            text_vector = self.encode_text(text)
                            self.document_embeddings.append(text_vector)
                            self.documents.append((text, metadata))
                        except Exception as e:
                            logger.error(f"处理文档 {i} 时发生错误: {str(e)}")
                            continue
                    
                    # 更新FAISS索引
                    if self.document_embeddings:
                        vectors = np.array(self.document_embeddings)
                        self.index.reset()
                        self.index.add(vectors.astype('float32'))
                    
                    logger.info(f"从旧格式转换并加载数据: {data_path}")
                    logger.info(f"加载了 {len(self.documents)} 个文档")
                else:
                    logger.error(f"不支持的数据格式: {data_path}")
                    return
                    
            else:
                logger.warning(f"数据文件不存在: {data_path}")
                
        except Exception as e:
            logger.error(f"加载向量存储失败: {str(e)}")
            logger.error(traceback.format_exc())
            
    def get_document_stats(self, file_path: str) -> Dict[str, Any]:
        """获取指定文档的统计信息
        
        Args:
            file_path: 文档路径
            
        Returns:
            Dict[str, Any]: 文档统计信息
        """
        try:
            # 统计该文档的文本块数量
            chunks = 0
            for _, metadata in self.documents:
                if metadata.get('source') == str(file_path):
                    chunks += 1
                    
            return {
                'chunks': chunks
            }
        except Exception as e:
            logger.error(f"获取文档统计信息失败 {file_path}: {str(e)}")
            return {
                'chunks': 0
            }

    def get_statistics(self) -> Dict[str, Any]:
        """获取向量存储的统计信息"""
        try:
            # 获取所有文档的源文件路径
            unique_sources = set()
            for _, metadata in self.documents:
                if 'source' in metadata:
                    unique_sources.add(metadata['source'])
            
            stats = {
                "total_documents": len(unique_sources),  # 使用唯一源文件数作为文档总数
                "total_chunks": len(self.documents),     # 文本块总数
                "vector_dimension": self.model.get_sentence_embedding_dimension() if self.model else 0,
                "index_size": self.index.ntotal if self.index else 0,
                "documents": []  # 文档列表
            }
            
            # 统计每个文档的文本块数量
            doc_chunks = {}
            for _, metadata in self.documents:
                if 'source' in metadata:
                    source = metadata['source']
                    doc_chunks[source] = doc_chunks.get(source, 0) + 1
            
            # 构建文档列表
            for source in unique_sources:
                stats["documents"].append({
                    "path": source,
                    "chunk_count": doc_chunks.get(source, 0)
                })
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "vector_dimension": 0,
                "index_size": 0,
                "documents": []
            }

    def delete_document(self, file_path: str) -> bool:
        """删除指定的文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 找到所有属于该文档的文本块
            new_documents = []
            new_embeddings = []
            
            # 遍历所有文本块，保留不属于被删除文档的块
            for i, (text, metadata) in enumerate(self.documents):
                if metadata.get('source') != str(file_path):
                    new_documents.append((text, metadata))
                    if self.document_embeddings is not None:
                        new_embeddings.append(self.document_embeddings[i])
            
            # 更新文档列表和向量
            self.documents = new_documents
            if new_embeddings:
                self.document_embeddings = np.array(new_embeddings)
                
                # 重建索引
                self.index.reset()
                if len(new_embeddings) > 0:
                    self.index.add(self.document_embeddings)
                    
            logger.info(f"文档删除成功，路径: {file_path}")
            logger.info(f"删除后的统计信息: {self.get_statistics()}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def delete_text_blocks(self, indices: List[int]) -> bool:
        """删除指定索引的文本块
        
        Args:
            indices: 要删除的文本块索引列表（从0开始）
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if not indices:
                logger.warning("没有指定要删除的文本块索引")
                return True
            
            # 验证索引范围
            max_index = len(self.documents) - 1
            invalid_indices = [idx for idx in indices if idx < 0 or idx > max_index]
            if invalid_indices:
                logger.error(f"无效的索引: {invalid_indices}")
                return False
            
            # 按降序排序索引，避免删除时索引变化
            sorted_indices = sorted(indices, reverse=True)
            
            # 删除指定索引的文本块
            new_documents = []
            new_embeddings = []
            
            for i, (text, metadata) in enumerate(self.documents):
                if i not in indices:
                    new_documents.append((text, metadata))
                    if self.document_embeddings is not None:
                        new_embeddings.append(self.document_embeddings[i])
            
            # 更新文档列表和向量
            self.documents = new_documents
            if new_embeddings:
                self.document_embeddings = np.array(new_embeddings)
                
                # 重建索引
                self.index.reset()
                if len(new_embeddings) > 0:
                    self.index.add(self.document_embeddings)
                    
            logger.info(f"成功删除 {len(indices)} 个文本块，索引: {indices}")
            logger.info(f"删除后的统计信息: {self.get_statistics()}")
            return True
            
        except Exception as e:
            logger.error(f"删除文本块失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def update_text_block(self, index: int, new_text: str) -> bool:
        """
        更新指定索引的文本块内容，并同步更新向量。
        Args:
            index: 文本块索引（从0开始）
            new_text: 新的文本内容
        Returns:
            bool: 是否更新成功
        """
        try:
            if index < 0 or index >= len(self.documents):
                logger.error(f"文本块索引超出范围: {index}")
                return False
            # 更新文本内容
            old_text, metadata = self.documents[index]
            self.documents[index] = (new_text, metadata)
            # 重新生成向量
            embedding = self.model.encode([new_text], convert_to_tensor=True).cpu().numpy()[0]
            self.document_embeddings[index] = embedding
            # 重建FAISS索引
            self.index.reset()
            if len(self.document_embeddings) > 0:
                self.index.add(self.document_embeddings)
            logger.info(f"成功更新文本块索引 {index} 的内容和向量")
            return True
        except Exception as e:
            logger.error(f"更新文本块失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False 