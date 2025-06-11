from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import os

class DocumentManager:
    """管理原始文档的类"""
    
    def __init__(self, storage_path: str = "data/documents.json"):
        """
        初始化文档管理器
        
        Args:
            storage_path: 文档信息存储路径
        """
        self.storage_path = storage_path
        self.documents: List[Dict] = []
        self._load_documents()
        
    def _load_documents(self):
        """从存储文件加载文档信息"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
        except Exception as e:
            print(f"加载文档信息失败: {e}")
            self.documents = []
            
    def _save_documents(self):
        """保存文档信息到存储文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文档信息失败: {e}")
            
    def add_document(self, file_path: str, chunk_count: int) -> bool:
        """
        添加文档记录
        
        Args:
            file_path: 文档路径
            chunk_count: 文本块数量
            
        Returns:
            bool: 是否添加成功
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False
                
            # 检查文档是否已存在
            for doc in self.documents:
                if doc['path'] == str(path):
                    # 更新现有文档信息
                    doc.update({
                        'size': path.stat().st_size,
                        'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                        'chunk_count': chunk_count,
                        'last_updated': datetime.now().isoformat()
                    })
                    self._save_documents()
                    return True
                    
            # 添加新文档记录
            doc_info = {
                'id': len(self.documents),
                'path': str(path),
                'name': path.name,
                'type': path.suffix.lower()[1:],  # 去掉前面的点
                'size': path.stat().st_size,
                'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                'chunk_count': chunk_count,
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self.documents.append(doc_info)
            self._save_documents()
            return True
            
        except Exception as e:
            print(f"添加文档记录失败: {e}")
            return False
            
    def remove_document(self, file_path: str) -> bool:
        """
        删除文档记录
        
        Args:
            file_path: 文档路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            path = str(Path(file_path))
            self.documents = [doc for doc in self.documents if doc['path'] != path]
            self._save_documents()
            return True
        except Exception as e:
            print(f"删除文档记录失败: {e}")
            return False
            
    def get_document(self, file_path: str) -> Optional[Dict]:
        """
        获取文档信息
        
        Args:
            file_path: 文档路径
            
        Returns:
            Optional[Dict]: 文档信息，如果不存在返回None
        """
        path = str(Path(file_path))
        for doc in self.documents:
            if doc['path'] == path:
                return doc
        return None
        
    def get_all_documents(self) -> List[Dict]:
        """
        获取所有文档信息
        
        Returns:
            List[Dict]: 文档信息列表
        """
        return self.documents
        
    def get_total_documents(self) -> int:
        """
        获取文档总数
        
        Returns:
            int: 文档总数
        """
        return len(self.documents)
        
    def get_total_chunks(self) -> int:
        """
        获取所有文档的文本块总数
        
        Returns:
            int: 文本块总数
        """
        return sum(doc.get('chunk_count', 0) for doc in self.documents) 