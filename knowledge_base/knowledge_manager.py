import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self, config):
        """初始化"""
        # 设置日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        self.config = config
        self.documents = []
    
    async def import_crawled_data(self) -> None:
        """导入爬取的数据"""
        try:
            raw_data_dir = Path(self.config.STORAGE_PATHS["raw_data"])
            
            # 确保目录存在
            raw_data_dir.mkdir(parents=True, exist_ok=True)
            
            # 遍历所有 JSON 文件
            for file_path in raw_data_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.documents.extend(data)
                        else:
                            self.documents.append(data)
                except Exception as e:
                    self.logger.warning(f"处理文件 {file_path} 时出错: {str(e)}")
                    continue
            
            self.logger.info(f"成功导入 {len(self.documents)} 条数据")
            
        except Exception as e:
            self.logger.error(f"导入数据时出错: {str(e)}")
            raise
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档"""
        return self.documents