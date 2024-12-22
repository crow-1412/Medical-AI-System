from typing import List, Dict, Any
import json
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

class KnowledgeManager:
    def __init__(self, config):
        self.config = config
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []
        self.medical_rules = {
            "高血压": {
                "levels": {
                    "1级": "140-159/90-99mmHg",
                    "2级": "160-179/100-109mmHg",
                    "3级": "≥180/≥110mmHg"
                },
                "risk_factors": [
                    "年龄>55岁",
                    "吸烟",
                    "血脂异常",
                    "肥胖",
                    "家族史"
                ],
                "complications": [
                    "心脏病",
                    "脑卒中",
                    "肾病"
                ]
            }
        }
        
    async def initialize(self):
        """初始化知识库"""
        try:
            self._load_documents()
            if self.documents:  # 只在有文档时构建索引
                self._build_index()
            else:
                logger.warning("没有找到文档数据，跳过索引构建")
        except Exception as e:
            logger.error(f"初始化知识库失败: {str(e)}")
            raise
        
    def _load_documents(self):
        """加载文档数据"""
        diseases_path = self.config.STORAGE_PATHS["diseases"]
        if diseases_path.exists():
            logger.info(f"从 {diseases_path} 加载文档")
            with open(diseases_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self.documents.append(json.loads(line))
        else:
            logger.warning(f"文档路径不存在: {diseases_path}")
                    
    def _build_index(self):
        """构建向量索引"""
        if not self.documents:
            logger.warning("没有文档数据，无法构建索引")
            return
            
        try:
            # 编码文档
            texts = [doc["content"] for doc in self.documents]
            embeddings = self.encoder.encode(texts)
            
            # 获��向量维度
            vector_dim = embeddings.shape[1]
            logger.info(f"向量维度: {vector_dim}")
            
            # 构建FAISS索引
            self.index = faiss.IndexFlatL2(vector_dim)  # 使用实际的向量维度
            
            # 添加向量到索引
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
            
            logger.info(f"成功构建索引，包含 {len(self.documents)} 个文档")
            
        except Exception as e:
            logger.error(f"构建索引失败: {str(e)}")
            raise
        
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        if not self.index:
            logger.warning("索引未初始化，无法执行搜索")
            return []
            
        try:
            # 编码查询
            query_vector = self.encoder.encode([query])[0]
            
            # 搜索最相关的文档
            distances, indices = self.index.search(
                np.array([query_vector]).astype('float32'), 
                k
            )
            
            # 返回结果
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.documents) and distance < self.config.KNOWLEDGE_BASE_CONFIG["similarity_threshold"]:
                    results.append(self.documents[idx])
                    
            logger.info(f"查询 '{query}' 找到 {len(results)} 个相关文档")
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise 

    async def import_crawled_data(self):
        """导入爬取的数据到知识库"""
        raw_data_path = self.config.STORAGE_PATHS["raw_data"]
        
        for file_path in raw_data_path.glob("*.jsonl"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line)
                        # 处理并存储数据
                        processed_data = self._process_medical_data(data)
                        if processed_data:
                            self.documents.append(processed_data)
                            
                # 更新向量索引
                self._update_index()
                
            except Exception as e:
                logger.error(f"导入数据失败 {file_path}: {str(e)}")
                
    def _process_medical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理医疗数据"""
        # 实现数据处理逻辑
        return processed_data
        
    async def analyze_symptoms(self, symptoms: list) -> dict:
        """分析症状关联性"""
        analysis = {
            "primary_symptoms": [],
            "secondary_symptoms": [],
            "risk_level": "",
            "related_diseases": []
        }
        
        # 实现症状分析逻辑
        return analysis
        
    async def generate_treatment_plan(self, diagnosis: str, symptoms: list) -> dict:
        """生成治疗方案"""
        plan = {
            "medications": [],
            "lifestyle_changes": [],
            "follow_up": "",
            "precautions": []
        }
        
        # 实现治疗方案生成逻辑
        return plan