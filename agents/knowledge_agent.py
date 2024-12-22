from typing import List, Dict, Any
from .base_agent import BaseAgent
from knowledge_base.vector_store import VectorStoreManager
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from langchain_community.embeddings import OpenAIEmbeddings

class KnowledgeAgent(BaseAgent):
    def __init__(self, config, vector_store: VectorStoreManager):
        super().__init__(config.MODEL_CONFIG["knowledge_agent"])
        self.vector_store = vector_store
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        # 从向量存储中检索相关上下文
        context = self.vector_store.search(query)
        
        return {
            "context": context
        }
        
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        return "\n".join([doc.page_content for doc in docs])
        
    async def _generate_response(self, query: str, context: str) -> str:
        prompt = f"基于以下参考信息回答问题：\n\n{context}\n\n问题：{query}\n回答："
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_return_sequences=1,
                temperature=0.7
            )
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response 