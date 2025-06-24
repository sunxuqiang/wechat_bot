from .base_processor import BaseFileProcessor
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TextProcessor(BaseFileProcessor):
    """文本文件处理器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.txt', '.md', '.csv']
        
        # 检查是否启用AI分块
        from config_loader import config
        self.enable_ai_chunking = config.getboolean('api', 'enable_ai_chunking', fallback=True)
        
        # 尝试导入AI分块服务
        if self.enable_ai_chunking:
            try:
                from ai_chunk_service import AIChunkService
                self.ai_chunk_service = AIChunkService()
                self.ai_available = True
                logger.info("AI分块服务初始化成功")
            except Exception as e:
                self.ai_chunk_service = None
                self.ai_available = False
                logger.warning(f"AI分块服务初始化失败，将使用传统分块方法: {str(e)}")
        else:
            self.ai_chunk_service = None
            self.ai_available = False
            logger.info("AI分块功能已禁用，将使用传统分块方法")
        
    def can_process(self, file_path: str) -> bool:
        """检查是否可以处理该文件"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """处理文本文件"""
        try:
            # 获取文件元数据
            metadata = self.get_file_metadata(file_path)
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 分割文本
            chunks = self.split_text_with_ai_fallback(content)
            
            # 创建文本块
            return [self.create_chunk(chunk, metadata) for chunk in chunks]
            
        except Exception as e:
            logger.error(f"处理文本文件失败: {str(e)}")
            return []

    def split_text_with_ai_fallback(self, text: str) -> List[str]:
        """使用AI分块，失败时回退到传统分块方法"""
        if not text:
            return []
        
        # 预处理文本
        text = text.strip()
        if not text:
            return []
        
        logger.info(f"开始处理文本，长度: {len(text)} 字符")
        
        # 尝试使用AI分块
        if self.ai_available and self.ai_chunk_service:
            try:
                logger.info("尝试使用AI模型进行智能分块")
                logger.info(f"发送文本到AI服务，文本长度: {len(text)} 字符")
                
                ai_chunks = self.ai_chunk_service.chunk_with_ai(text)
                
                if ai_chunks:
                    logger.info(f"AI服务返回 {len(ai_chunks)} 个分块结果")
                    
                    if self.ai_chunk_service.validate_chunks(ai_chunks):
                        # AI分块成功，提取文本内容
                        text_chunks = self.ai_chunk_service.extract_text_content(ai_chunks)
                        if text_chunks:
                            logger.info(f"AI分块成功，生成 {len(text_chunks)} 个文本块")
                            for i, chunk in enumerate(text_chunks[:3]):  # 只显示前3个块
                                logger.info(f"  块 {i+1}: {chunk[:50]}...")
                            return text_chunks
                        else:
                            logger.warning("AI分块结果为空，回退到传统分块方法")
                    else:
                        logger.warning("AI分块结果验证失败，回退到传统分块方法")
                        # 记录验证失败的详细信息
                        for i, chunk in enumerate(ai_chunks):
                            if isinstance(chunk, dict):
                                content = chunk.get('content', '')
                                logger.warning(f"  块 {i+1}: 长度={len(content)}字符, 内容预览={content[:50]}...")
                else:
                    logger.warning("AI服务返回空结果，回退到传统分块方法")
                    
            except Exception as e:
                logger.error(f"AI分块过程中发生错误: {str(e)}")
                import traceback
                logger.error(f"错误详情: {traceback.format_exc()}")
                logger.info("回退到传统分块方法")
        else:
            logger.info("AI分块服务不可用，使用传统分块方法")
        
        # 使用传统分块方法
        logger.info("使用传统分块方法")
        return self.split_text_advanced(text)

    def split_text_advanced(self, text: str) -> List[str]:
        """高级文本分割方法，支持多种分割策略"""
        if not text:
            return []
        
        # 预处理文本
        text = text.strip()
        if not text:
            return []
        
        # 尝试多种分割策略
        chunks = []
        
        # 策略1: 按段落分割（双换行）
        if '\n\n' in text:
            chunks = self._split_by_paragraphs(text)
            if chunks and len(chunks) > 1:
                logger.info(f"使用段落分割策略，分割出 {len(chunks)} 个段落")
                return chunks
        
        # 策略2: 按序号分割
        if self._has_numbered_items(text):
            chunks = self._split_by_numbers(text)
            if chunks and len(chunks) > 1:
                logger.info(f"使用序号分割策略，分割出 {len(chunks)} 个条目")
                return chunks
        
        # 策略3: 按标题分割
        if self._has_headings(text):
            chunks = self._split_by_headings(text)
            if chunks and len(chunks) > 1:
                logger.info(f"使用标题分割策略，分割出 {len(chunks)} 个章节")
                return chunks
        
        # 策略4: 按句子分割
        chunks = self._split_by_sentences(text)
        logger.info(f"使用句子分割策略，分割出 {len(chunks)} 个句子块")
        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:  # 提高最小长度阈值
                # 如果段落太长，进一步分割
                if len(para) > self.chunk_size * 2:
                    sub_chunks = self._split_long_paragraph(para)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(para)
        
        return chunks

    def _split_by_numbers(self, text: str) -> List[str]:
        """按序号分割文本"""
        # 匹配各种序号格式：1. 2. 3. 或 1) 2) 3) 或 一、二、三、等
        number_patterns = [
            r'\n\s*(\d+\.)\s+',  # 1. 2. 3.
            r'\n\s*(\d+\))\s+',  # 1) 2) 3)
            r'\n\s*([一二三四五六七八九十]+、)\s+',  # 一、二、三、
            r'\n\s*([①②③④⑤⑥⑦⑧⑨⑩]+)\s+',  # ①②③④⑤
            r'\n\s*([A-Z]\.)\s+',  # A. B. C.
            r'\n\s*([a-z]\.)\s+',  # a. b. c.
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, text):
                # 使用该模式分割
                parts = re.split(pattern, text)
                chunks = []
                current_chunk = ""
                
                for i, part in enumerate(parts):
                    if i == 0:  # 第一部分（序号前的内容）
                        if part.strip() and len(part.strip()) > 20:
                            current_chunk = part.strip()
                    else:
                        # 偶数索引是序号，奇数索引是内容
                        if i % 2 == 1:  # 序号
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = part + " " + (parts[i+1] if i+1 < len(parts) else "")
                        elif i % 2 == 0:  # 内容
                            current_chunk += " " + part
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 清理和验证chunks，合并过短的块
                cleaned_chunks = self._merge_short_chunks(chunks)
                return cleaned_chunks
        
        return []

    def _split_by_headings(self, text: str) -> List[str]:
        """按标题分割文本"""
        # 匹配各种标题格式
        heading_patterns = [
            r'\n\s*(第[一二三四五六七八九十\d]+[章节条])\s*[：:]\s*',  # 第一章： 第一节：
            r'\n\s*([一二三四五六七八九十\d]+[、.．]\s*[^\n]+)\s*\n',  # 一、标题 1.标题
            r'\n\s*([A-Z][A-Z\s]*[：:]\s*[^\n]+)\s*\n',  # 标题：内容
            r'\n\s*([^\n]+[：:]\s*[^\n]+)\s*\n',  # 通用标题格式
        ]
        
        for pattern in heading_patterns:
            if re.search(pattern, text):
                parts = re.split(pattern, text)
                chunks = []
                current_chunk = ""
                
                for i, part in enumerate(parts):
                    if i == 0:  # 第一部分
                        if part.strip() and len(part.strip()) > 20:
                            current_chunk = part.strip()
                    else:
                        # 偶数索引是标题，奇数索引是内容
                        if i % 2 == 1:  # 标题
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = part + " " + (parts[i+1] if i+1 < len(parts) else "")
                        elif i % 2 == 0:  # 内容
                            current_chunk += " " + part
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 清理和验证chunks，合并过短的块
                cleaned_chunks = self._merge_short_chunks(chunks)
                return cleaned_chunks
        
        return []

    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子分割文本"""
        # 使用基础处理器的分割方法，但优化句子边界
        return self.split_text(text)

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割过长的段落"""
        if len(paragraph) <= self.chunk_size:
            return [paragraph]
        
        chunks = []
        start = 0
        
        while start < len(paragraph):
            end = start + self.chunk_size
            
            if end >= len(paragraph):
                chunk = paragraph[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # 寻找句子边界
            sentence_endings = ['。', '！', '？', '.', '!', '?', '\n']
            best_end = end
            
            for ending in sentence_endings:
                pos = paragraph.rfind(ending, start, end)
                if pos > start + self.chunk_size * 0.7:  # 确保不会产生太小的块
                    best_end = pos + len(ending)
                    break
            
            chunk = paragraph[start:best_end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(best_end - self.chunk_overlap, start + 1)
            
            if start >= len(paragraph):
                break
        
        return chunks

    def _has_numbered_items(self, text: str) -> bool:
        """检查文本是否包含序号"""
        number_patterns = [
            r'\n\s*\d+\.\s+',  # 1. 2. 3.
            r'\n\s*\d+\)\s+',  # 1) 2) 3)
            r'\n\s*[一二三四五六七八九十]+、\s+',  # 一、二、三、
            r'\n\s*[①②③④⑤⑥⑦⑧⑨⑩]+\s+',  # ①②③④⑤
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _has_headings(self, text: str) -> bool:
        """检查文本是否包含标题"""
        heading_patterns = [
            r'\n\s*第[一二三四五六七八九十\d]+[章节条]\s*[：:]',  # 第一章： 第一节：
            r'\n\s*[一二三四五六七八九十\d]+[、.．]\s*[^\n]+\s*\n',  # 一、标题 1.标题
            r'\n\s*[A-Z][A-Z\s]*[：:]\s*[^\n]+\s*\n',  # 标题：内容
        ]
        
        for pattern in heading_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _merge_short_chunks(self, chunks: List[str]) -> List[str]:
        """合并过短的文本块"""
        if not chunks:
            return []
        
        merged_chunks = []
        current_chunk = ""
        
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
                
            # 如果当前块太短，尝试合并
            if len(chunk) < 30:  # 提高最小长度阈值
                if current_chunk:
                    current_chunk += " " + chunk
                else:
                    current_chunk = chunk
            else:
                # 如果当前块足够长，保存之前的合并块
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        # 添加最后一个块
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        # 最终过滤，确保所有块都有合理长度
        final_chunks = []
        for chunk in merged_chunks:
            if len(chunk) >= 20:  # 最终长度检查
                final_chunks.append(chunk)
        
        return final_chunks 