import asyncio
import logging
from pathlib import Path
from config.config import Config
from knowledge_base.knowledge_manager import KnowledgeManager
from knowledge_base.vector_store import VectorStoreManager
from training.lora_trainer import LoRATrainer
from agents.report_generation_agent import ReportGenerationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalSystemProcessor:
    def __init__(self):
        self.config = Config
        self.knowledge_mgr = KnowledgeManager(self.config)
        self.vector_store = VectorStoreManager(self.config)
        
    async def process_knowledge_base(self):
        """处理知识库数据"""
        logger.info("开始处理知识库数据...")
        
        # 1. 初始化知识管理器
        await self.knowledge_mgr.initialize()
        
        # 2. 导入爬取的数据
        await self.knowledge_mgr.import_crawled_data()
        
        # 3. 构建向量索引
        self.vector_store.initialize_store()
        
        logger.info("知识库处理完成")
        
    async def prepare_training_data(self):
        """准备训练数据"""
        logger.info("开始准备训练数据...")
        
        train_data = []
        raw_data_path = self.config.STORAGE_PATHS["raw_data"]
        
        try:
            for file in raw_data_path.glob("*.jsonl"):
                # 处理每个文件
                processed_data = await self.knowledge_mgr.process_medical_data(file)
                if processed_data:
                    # 转换为训练格式
                    for item in processed_data:
                        train_example = {
                            "text": f"标题：{item['title']}\n内容：{item['content']}",
                            "source": item['source'],
                            "type": item['type']
                        }
                        train_data.append(train_example)
                
            logger.info(f"准备了 {len(train_data)} 条训练数据")
            return train_data
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {str(e)}")
            raise
        
    async def train_model(self):
        """训练模型"""
        logger.info("开始模型训练...")
        
        try:
            # 1. 准备训练数据
            train_data = await self.prepare_training_data()
            
            # 2. 初始化LoRA训练器
            trainer = LoRATrainer(self.config)
            
            # 3. 开始训练
            trainer.train(
                train_dataset=train_data,
                output_dir=str(self.config.STORAGE_ROOT / "lora_weights")  # 转换为字符串
            )
            
            logger.info("模型训练完成")
            
        except Exception as e:
            logger.error(f"训练失败: {str(e)}")
            raise
        
    async def run(self):
        """运行完整流程"""
        try:
            # 1. 处理知识库
            await self.process_knowledge_base()
            
            # 2. 训练模型
            await self.train_model()
            
            # 3. 测试生成效果
            await self.test_generation()
            
        except Exception as e:
            logger.error(f"处理过程出错: {str(e)}", exc_info=True)
            
    async def test_generation(self):
        """测试报告生成效果"""
        test_cases = [
            {
                "patient_info": "患者，男，45岁，血压160/100mmHg，头痛、眩晕、乏力、心悸、胸闷、呼吸急促等症状。",
                "report_type": "初步诊断报告"
            }
        ]
        
        agent = ReportGenerationAgent(self.config)
        
        for case in test_cases:
            result = await agent.process(case)
            logger.info(f"\n生成报告:\n{result['data']['report']}")

async def main():
    processor = MedicalSystemProcessor()
    await processor.run()

if __name__ == "__main__":
    asyncio.run(main()) 