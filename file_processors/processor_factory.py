from typing import List, Type
from .base_processor import BaseFileProcessor
from .text_processor import TextProcessor
from .pdf_processor import PDFProcessor
from .word_processor import WordProcessor
from .excel_processor import ExcelProcessor

class ProcessorFactory:
    """文件处理器工厂"""
    
    def __init__(self):
        self.processors: List[BaseFileProcessor] = [
            TextProcessor(),
            PDFProcessor(),
            WordProcessor(),
            ExcelProcessor()
        ]
        
    def get_processor(self, file_path: str) -> BaseFileProcessor:
        """获取适合的处理器"""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        return None 