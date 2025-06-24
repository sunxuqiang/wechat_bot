from .base_processor import BaseFileProcessor
import logging
from typing import List, Dict, Any
import PyPDF2
import re

logger = logging.getLogger(__name__)

class PDFProcessor(BaseFileProcessor):
    """PDF文件处理器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pdf']
        
    def can_process(self, file_path: str) -> bool:
        """检查是否可以处理该文件"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """处理PDF文件（AI智能分块）"""
        print('当前加载的 pdf_processor.py 路径:', __file__)
        try:
            from ai_chunk_service import AIChunkService
            # 获取文件元数据
            metadata = self.get_file_metadata(file_path)
            # 读取PDF文件
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
            
            # 类型检查和清理
            content = self._clean_text(content)
            print(f"PDF原始合并文本类型: {type(content)}, 长度: {len(content)}")
            if not isinstance(content, str):
                raise TypeError(f"PDF内容不是str, 而是{type(content)}")
                
            # AI智能分块
            ai_service = AIChunkService()
            max_ai_chars = 3000
            chunks = []
            start = 0
            chunk_idx = 1
            
            while start < len(content):
                start = int(start)
                end = int(start + int(max_ai_chars))
                print(f"PDF AI分块循环: 第{chunk_idx}块, start={start}, end={end}, max_ai_chars={max_ai_chars}")
                
                # 找到单词边界
                if end < len(content):
                    # 向后查找空格或标点作为单词边界
                    word_boundary = self._find_word_boundary(content, end)
                    if word_boundary > end:
                        end = word_boundary
                    
                sub_text = content[start:end]
                
                # 在句子边界处分割
                if end < len(content):
                    last_sentence = self._find_last_sentence_boundary(sub_text)
                    if last_sentence > 0 and last_sentence > max_ai_chars * 0.5:
                        sub_text = sub_text[:last_sentence]
                
                print(f"正在AI分块第{chunk_idx}块，文本长度: {len(sub_text)} 字符")
                ai_chunks = ai_service.chunk_with_ai(sub_text)
                
                if ai_chunks:
                    for ai_chunk in ai_chunks:
                        ai_content = ai_chunk.get('content', '').strip()
                        if ai_content:
                            ai_metadata = dict(metadata)
                            ai_metadata['type'] = 'pdf_ai'
                            chunks.append(self.create_chunk(ai_content, ai_metadata))
                
                if len(sub_text) == 0:
                    start += max_ai_chars
                else:
                    start += len(sub_text)
                chunk_idx += 1
            
            return chunks
            
        except Exception as e:
            import traceback
            logger.error(f"处理PDF文件失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    def _clean_text(self, text: str) -> str:
        """清理文本，移除特殊字符但保留单词完整性"""
        # 移除控制字符和特殊Unicode字符
        text = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F\uFEFF\x00-\x1F]', '', text)
        # 规范化空白字符，但保留段落分隔
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
        
    def _find_word_boundary(self, text: str, pos: int) -> int:
        """在指定位置附近找到单词边界"""
        # 定义单词边界字符
        boundaries = ' \n\t.,!?;:)]}'
        # 向后查找最近的单词边界
        for i in range(pos, min(pos + 50, len(text))):
            if text[i] in boundaries:
                return i
        return pos
        
    def _find_last_sentence_boundary(self, text: str) -> int:
        """找到最后一个完整句子的边界"""
        # 中英文标点符号
        sentence_ends = ['。', '.', '!', '?', '！', '？', '\n\n']
        last_pos = -1
        
        for end in sentence_ends:
            pos = text.rfind(end)
            if pos > last_pos:
                last_pos = pos + len(end)
                
        return last_pos if last_pos > 0 else -1 