import os
import json
import logging
import asyncio
from pathlib import Path

from config.config import Config
from knowledge_base.knowledge_manager import KnowledgeManager
from training.lora_trainer import LoRATrainer

class MedicalSystemProcessor:
    """医疗系统处理器"""
    
    def __init__(self):
        """初始化"""
        self.config = Config()
        self.config.init_dirs()
        
        self._setup_logging()
        self.knowledge_mgr = KnowledgeManager(self.config)
        self.trainer = LoRATrainer(self.config)
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config.STORAGE_PATHS["logs"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=self.config.LOG_FORMAT,
            handlers=[
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    async def process_knowledge_base(self):
        """处理知识库"""
        try:
            self.logger.info("开始处理知识库数据...")
            await self.knowledge_mgr.import_crawled_data()
            self.logger.info("知识库处理完成")
            
        except Exception as e:
            self.logger.error(f"处理知识库时出错: {str(e)}")
            raise
    
    async def prepare_training_data(self):
        """准备训练数据"""
        try:
            self.logger.info("开始准备训练数据...")
            
            # 从知识库中获取数据
            data = await self.knowledge_mgr.get_all_documents()
            
            # 保存为训练数据文件
            train_data_path = Path(self.config.STORAGE_PATHS["processed_data"]) / "train_data.jsonl"
            train_data_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(train_data_path, 'w', encoding='utf-8') as f:
                for item in data:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
            
            self.logger.info(f"准备了 {len(data)} 条训练数据")
            return str(train_data_path)
            
        except Exception as e:
            self.logger.error(f"准备训练数据时出错: {str(e)}")
            raise
    
    async def train_model(self):
        """训练模型"""
        try:
            self.logger.info("开始模型训练...")
            
            # 准备训练数据
            train_data_path = await self.prepare_training_data()
            
            # 准备模型
            self.trainer.prepare_model()
            
            # 开始训练
            self.trainer.train(train_data_path)
            
        except Exception as e:
            self.logger.error(f"训练失败: {str(e)}")
            raise
    
    async def run(self):
        """运行处理流程"""
        try:
            # 处理知识库
            await self.process_knowledge_base()
            
            # 训练模型
            await self.train_model()
            
        except Exception as e:
            self.logger.error(f"处理过程出错: {str(e)}")
            raise

async def main():
    """主函数"""
    processor = MedicalSystemProcessor()
    await processor.run()

if __name__ == "__main__":
    asyncio.run(main()) 