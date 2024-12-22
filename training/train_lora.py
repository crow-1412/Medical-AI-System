from training.lora_trainer import LoRATrainer
import asyncio

async def train_model():
    # 准备训练数据
    knowledge_mgr = KnowledgeManager(Config)
    await knowledge_mgr.initialize()
    train_data = await knowledge_mgr.prepare_training_data()
    
    # 初始化LoRA训练器
    trainer = LoRATrainer(Config)
    
    # 加载基础模型
    trainer.setup_lora(model)
    
    # 开始训练
    trainer.train(
        train_dataset=train_data,
        output_dir=Config.STORAGE_ROOT / "lora_weights"
    )

if __name__ == "__main__":
    asyncio.run(train_model()) 