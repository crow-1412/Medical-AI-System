from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from typing import List, Dict, Any
from config.config import Config

class VectorStoreManager:
    def __init__(self, config):
        self.config = config
        self.embeddings = OpenAIEmbeddings(verify=False)
        self.vector_store = None
        
    def initialize_store(self):
        self.vector_store = Chroma(
            persist_directory=str(self.config.VECTOR_DB_PATH),
            embedding_function=self.embeddings
        )
        
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.vector_store:
            self.initialize_store()
        return await self.vector_store.similarity_search_async(query, k=k)