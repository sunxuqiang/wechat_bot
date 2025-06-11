import requests
import json
from typing import Dict, List, Any, Optional

class MaxKBClient:
    """MaxKB API 客户端"""
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        初始化 MaxKB 客户端
        
        Args:
            base_url: MaxKB 服务器地址，例如 http://localhost:8080
            api_key: API密钥（如果需要）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def query_knowledge_base(self, question: str, kb_id: str) -> Dict[str, Any]:
        """
        查询知识库
        
        Args:
            question: 用户问题
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/knowledge/{kb_id}/query",
                json={
                    "query": question
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"查询知识库失败: {e}")
            return {"error": str(e)}
    
    def upload_document(self, kb_id: str, file_path: str) -> Dict[str, Any]:
        """
        上传文档到知识库
        
        Args:
            kb_id: 知识库ID
            file_path: 文档路径
            
        Returns:
            Dict[str, Any]: 上传结果
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(
                    f"{self.base_url}/api/knowledge/{kb_id}/documents",
                    files=files
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"上传文档失败: {e}")
            return {"error": str(e)}
    
    def create_knowledge_base(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        创建知识库
        
        Args:
            name: 知识库名称
            description: 知识库描述
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/knowledge",
                json={
                    "name": name,
                    "description": description
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"创建知识库失败: {e}")
            return {"error": str(e)}
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        获取所有知识库列表
        
        Returns:
            List[Dict[str, Any]]: 知识库列表
        """
        try:
            response = self.session.get(f"{self.base_url}/api/knowledge")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取知识库列表失败: {e}")
            return [] 