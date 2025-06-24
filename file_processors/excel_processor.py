from .base_processor import BaseFileProcessor
import logging
from typing import List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

class ExcelProcessor(BaseFileProcessor):
    """Excel文件处理器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.xlsx', '.xls']
        
    def can_process(self, file_path: str) -> bool:
        """检查是否可以处理该文件"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """优化：每行一个文本块，支持多sheet，元数据丰富"""
        try:
            # 获取文件元数据
            base_metadata = self.get_file_metadata(file_path)
            # 读取所有sheet
            xls = pd.ExcelFile(file_path)
            chunks = []
            for sheet_name in xls.sheet_names:
                df = xls.parse(sheet_name)
                # 添加sheet表头块
                header_text = f"[Sheet: {sheet_name}]\n表头: " + ", ".join([str(col) for col in df.columns])
                header_metadata = base_metadata.copy()
                header_metadata.update({
                    'sheet': sheet_name,
                    'type': 'header',
                })
                chunks.append(self.create_chunk(header_text, header_metadata))
                # 遍历每一行
                for idx, row in df.iterrows():
                    row_items = [f"{col}: {row[col]}" for col in df.columns]
                    row_text = f"[Sheet: {sheet_name}] 第{idx+1}行 | " + " | ".join(row_items)
                    row_metadata = base_metadata.copy()
                    row_metadata.update({
                        'sheet': sheet_name,
                        'row': int(idx)+1,
                        'type': 'row',
                        'columns': list(df.columns)
                    })
                    chunks.append(self.create_chunk(row_text, row_metadata))
            return chunks
        except Exception as e:
            logger.error(f"处理Excel文件失败: {str(e)}")
            return [] 