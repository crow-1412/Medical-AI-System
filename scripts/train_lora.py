import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from training.lora_trainer import LoRATrainer
from config.config import Config

def main():
    """主函数"""
    try:
        # 创建必要的目录
        for path in Config.STORAGE_PATHS.values():
            os.makedirs(path, exist_ok=True)
            
        # 初始化训练器
        trainer = LoRATrainer(Config)
        
        # 准备模型
        trainer.prepare_model()
        
        # 训练数据路径
        train_data_path = os.path.join(Config.STORAGE_PATHS["processed_data"], "train.jsonl")
        eval_data_path = os.path.join(Config.STORAGE_PATHS["processed_data"], "eval.jsonl")
        test_data_path = os.path.join(Config.STORAGE_PATHS["processed_data"], "test.jsonl")
        
        # 开始训练
        trainer.train(train_data_path, eval_data_path)
        
        # 评估模型
        metrics = trainer.evaluate(test_data_path)
        print("\n评估结果:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"训练过程出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
