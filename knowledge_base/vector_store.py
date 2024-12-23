from typing import List, Dict, Any
from config.config import Config
import chromadb
from chromadb.config import Settings
from gensim.models.fasttext import FastText
import numpy as np

class VectorStoreManager:
    def __init__(self, config):
        self.config = config
        # 使用 FastText 替代 sentence-transformers
        self.model = FastText(vector_size=100)
        self.client = chromadb.PersistentClient(
            path=str(self.config.VECTOR_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
        
    def initialize_store(self):
        """初始化向量存储"""
        try:
            self.collection = self.client.get_or_create_collection(
                name="medical_knowledge",
                metadata={"description": "医疗知识库"}
            )
        except Exception as e:
            print(f"初始化向量存储失败: {str(e)}")
            raise
        
    def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        words = text.split()
        if not words:
            return np.zeros(100).tolist()
        vectors = [self.model.wv[word] for word in words if word in self.model.wv]
        if not vectors:
            return np.zeros(100).tolist()
        return np.mean(vectors, axis=0).tolist()
        
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            if not self.collection:
                self.initialize_store()
            
            # 生成查询向量
            query_embedding = self.get_embedding(query)
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            # 格式化结果
            documents = []
            for idx, (doc, score) in enumerate(zip(results['documents'][0], results['distances'][0])):
                documents.append({
                    'content': doc,
                    'score': float(score),
                    'metadata': results['metadatas'][0][idx] if results['metadatas'] else {}
                })
            
            return documents
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []