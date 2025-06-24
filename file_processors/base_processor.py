from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseFileProcessor(ABC):
    """文件处理器基类"""
    
    def __init__(self):
        self.supported_extensions = []
        # 从配置文件获取chunk设置，如果没有则使用默认值
        try:
            from config_loader import config
            self.chunk_size = int(config.getint('vector_store', 'chunk_size', 1000))
            self.chunk_overlap = int(config.getint('vector_store', 'chunk_overlap', 200))
        except:
            self.chunk_size = 1000
            self.chunk_overlap = 200
        print(f"[DEBUG] chunk_size={self.chunk_size} (type={type(self.chunk_size)}), chunk_overlap={self.chunk_overlap} (type={type(self.chunk_overlap)})")
        
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """检查是否可以处理该文件"""
        pass
        
    @abstractmethod
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """处理文件并返回文本块列表"""
        pass
        
    def split_text(self, text: str) -> List[str]:
        """将文本分割成块，优化中文文本处理"""
        if not text:
            return []
        
        # 预处理文本
        text = text.strip()
        if not text:
            return []
        
        # 定义中文分隔符（按优先级排序）
        separators = [
            '\n\n',  # 段落分隔
            '\n',    # 换行
            '。',    # 句号
            '！',    # 感叹号
            '？',    # 问号
            '；',    # 分号
            '：',    # 冒号
            '，',    # 逗号
            '.',     # 英文句号
            '!',     # 英文感叹号
            '?',     # 英文问号
            ';',     # 英文分号
            ':',     # 英文冒号
            ',',     # 英文逗号
        ]
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            end = int(end)
            
            if end >= text_length:
                # 到达文本末尾
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # 寻找最佳分割点
            best_end = end
            for separator in separators:
                # 在当前块范围内寻找分隔符
                pos = text.rfind(separator, start, end)
                if pos > start and pos < end:
                    # 找到分隔符，检查是否是一个好的分割点
                    if pos > start + self.chunk_size * 0.5:  # 确保不会产生太小的块
                        best_end = pos + len(separator)
                        break
            
            # 如果没找到合适的分隔符，尝试向前查找
            if best_end == end:
                for separator in separators:
                    # 这里加 int() 保证切片参数为整数
                    pos = text.find(separator, end, int(min(end + self.chunk_size * 0.3, text_length)))
                    if pos > end:
                        best_end = pos + len(separator)
                        break
            
            # 提取文本块
            chunk = text[start:best_end].strip()
            if chunk:
                # 进一步清理文本块
                chunk = self._clean_chunk(chunk)
                if chunk:
                    chunks.append(chunk)
            
            # 计算下一个起始位置（考虑重叠）
            start = max(best_end - self.chunk_overlap, start + 1)
            start = int(start)
            
            # 防止无限循环
            if start >= text_length:
                break
        
        return chunks

    def _clean_chunk(self, chunk: str) -> str:
        """清理文本块"""
        if not chunk:
            return ""
        
        # 移除多余的空白字符
        chunk = ' '.join(chunk.split())
        
        # 移除开头和结尾的标点符号
        chunk = chunk.strip('。！？；：，.!?;:,')
        
        # 确保块不为空且长度合理
        if len(chunk) < 10:  # 太短的块可能没有意义
            return ""
        
        return chunk
        
    def create_chunk(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """创建文本块"""
        return {
            "text": text,
            "metadata": metadata
        }
        
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文件元数据"""
        return {
            "source": file_path,
            "filename": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1].lower(),
            "file_size": os.path.getsize(file_path),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } 