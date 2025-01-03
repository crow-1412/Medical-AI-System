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
                "symptoms": {
                    "primary": ["头痛", "头晕", "眩晕"],
                    "secondary": ["心悸", "胸闷", "呼吸急促", "乏力"]
                },
                "risk_factors": ["年龄>45岁", "家族史阳性"],
                "treatments": {
                    "medications": [
                        "钙通道阻滞剂",
                        "血管紧张素转换酶抑制剂(ACEI)",
                        "血管紧张素受体拮抗剂(ARB)"
                    ],
                    "lifestyle": [
                        "限制盐摄入量（<6g/日）",
                        "规律运动（每周3-5次，每次30分钟）",
                        "戒烟限酒",
                        "保持健康体重"
                    ],
                    "follow_up": "每2周随访一次，直至血压稳定",
                    "precautions": [
                        "定期监测血压",
                        "避免剧烈运动",
                        "保持情绪稳定",
                        "遵医嘱服药"
                    ]
                }
            }
        }
        
    async def initialize(self):
        """初始化知识库"""
        try:
            # 1. 加载默认文档
            self._initialize_default_documents()
            logger.info(f"加载了 {len(self.documents)} 个默认文档")
            
            # 2. 尝试加载额外文档
            self._load_documents()
            
            # 3. 立即构建索引
            texts = [doc["content"] for doc in self.documents]
            if not texts:
                logger.warning("没有找到任何文档，创建空索引")
                # 创建空索引
                self.index = faiss.IndexFlatL2(384)  # 使用默认维度
            else:
                logger.info(f"开始为 {len(texts)} 个文档构建索引")
                embeddings = self.encoder.encode(texts)
                vector_dim = embeddings.shape[1]
                
                self.index = faiss.IndexFlatL2(vector_dim)
                embeddings_array = np.array(embeddings).astype('float32')
                self.index.add(embeddings_array)
                
                logger.info(f"索引构建完成，维度: {vector_dim}")
            
        except Exception as e:
            logger.error(f"初始化知识库失败: {str(e)}")
            # 确保即使出错也创建一个空索引
            self.index = faiss.IndexFlatL2(384)
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
            
            # 获向量维度
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
        try:
            if self.index is None:
                logger.warning("索引未初始化，创建空索引")
                self.index = faiss.IndexFlatL2(384)
                return []
            
            if self.index.ntotal == 0:
                logger.warning("索引为空，无法搜索")
                return []
            
            # 编码查询
            query_vector = self.encoder.encode([query])[0]
            
            # 搜索最相关的文档
            distances, indices = self.index.search(
                np.array([query_vector]).astype('float32'), 
                min(k, self.index.ntotal)  # 确保k不超过索引中的文档数
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
            return []

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
        try:
            processed_data = {
                "title": data.get("title", ""),
                "content": data.get("content", "") or data.get("abstract", ""),
                "source": data.get("source", ""),
                "url": data.get("url", ""),
                "type": data.get("type", "article"),
                "keyword": data.get("keyword", ""),
                "timestamp": data.get("crawl_time", "")
            }
            return processed_data
        except Exception as e:
            logger.error(f"处理数据失败: {str(e)}")
            return None

    async def process_medical_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理医疗数据文件"""
        processed_data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    processed = self._process_medical_data(data)
                    if processed:
                        processed_data.append(processed)
            return processed_data
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
            return []
        
    async def analyze_symptoms(self, symptoms: list, bp: str) -> dict:
        """分析症状和血压"""
        # 解析血压值
        systolic, diastolic = map(int, bp.split('/'))
        
        # 判断高血压等级
        if 160 <= systolic < 180 or 100 <= diastolic < 110:
            risk_level = "2级高血压"
        elif systolic >= 180 or diastolic >= 110:
            risk_level = "3级高血压"
        elif 140 <= systolic < 160 or 90 <= diastolic < 100:
            risk_level = "1级高血压"
        else:
            risk_level = "正常"

        return {
            "primary_symptoms": [s for s in symptoms if s in self.medical_rules["高血压"]["symptoms"]["primary"]],
            "secondary_symptoms": [s for s in symptoms if s in self.medical_rules["高血压"]["symptoms"]["secondary"]],
            "risk_level": risk_level,
            "related_diseases": ["高血压", "心血管疾病"]
        }
        
    async def generate_treatment_plan(self, diagnosis: str, symptoms: list) -> dict:
        """生成治疗方案"""
        try:
            # 获取高血压相关治疗方案
            hypertension_rules = self.medical_rules["高血压"]["treatments"]
            
            return {
                "medications": hypertension_rules["medications"],
                "lifestyle_changes": hypertension_rules["lifestyle"],
                "follow_up": hypertension_rules["follow_up"],
                "precautions": hypertension_rules["precautions"]
            }
        except Exception as e:
            logger.error(f"生成治疗方案失败: {str(e)}")
            return {
                "medications": [],
                "lifestyle_changes": [],
                "follow_up": "",
                "precautions": []
            }

    def _update_index(self):
        """更新向量索引"""
        try:
            # 重新构建索引
            texts = [doc["content"] for doc in self.documents]
            embeddings = self.encoder.encode(texts)
            
            # 获取向量维度
            vector_dim = embeddings.shape[1]
            
            # 创建新索引
            self.index = faiss.IndexFlatL2(vector_dim)
            
            # 添加向量到索引
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
            
            logger.info(f"索引更新完成，当前包含 {len(self.documents)} 个文档")
            
        except Exception as e:
            logger.error(f"更新索引失败: {str(e)}")
            raise

    def _initialize_default_documents(self):
        """初始化默认医学文档"""
        default_docs = [
            {
                "title": "高血压基础知识",
                "content": """高血压是常见的慢性病，主要表现为血压升高。诊断标准：
1. 收缩压≥140mmHg和/或舒张压≥90mmHg
2. 分级标准：
   - 1级：140-159/90-99mmHg
   - 2级：160-179/100-109mmHg
   - 3级：≥180/≥110mmHg""",
                "type": "knowledge"
            },
            {
                "title": "高血压症状",
                "content": """常见症状包括：
1. 头痛、头晕、眩晕
2. 心悸、胸闷、气短
3. 疲劳、乏力
4. 视物模糊
需要注意的是，部分患者可能无明显症状。""",
                "type": "symptoms"
            },
            {
                "title": "高血压治疗方案",
                "content": """治疗原则：
1. 药物治疗：钙通道阻滞剂、ACEI/ARB类药物
2. 生活方式干预：限盐、运动、戒烟限酒
3. 定期监测血压
4. 防治并发症""",
                "type": "treatment"
            }
        ]
        self.documents.extend(default_docs)