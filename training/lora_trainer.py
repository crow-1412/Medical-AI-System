import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModel,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    get_peft_model,
    LoraConfig,
    TaskType,
    prepare_model_for_kbit_training
)
from datasets import load_dataset

class MedicalDataset(Dataset):
    """医疗数据集类"""
    
    def __init__(self, data_path: str, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        
        # 加载数据
        self._load_data(data_path)
        
    def _load_data(self, data_path: str):
        """加载数据文件"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        # 构建训练样本
                        text = self._construct_training_text(item)
                        if text:
                            encoded = self.tokenizer(
                                text,
                                max_length=self.max_length,
                                padding='max_length',
                                truncation=True,
                                return_tensors='pt'
                            )
                            self.examples.append({
                                'input_ids': encoded['input_ids'].squeeze(),
                                'attention_mask': encoded['attention_mask'].squeeze()
                            })
                    except json.JSONDecodeError as e:
                        logging.warning(f"解析数据行失败: {str(e)}")
                        continue
                    except Exception as e:
                        logging.warning(f"处理数据样本时出错: {str(e)}")
                        continue
                        
            logging.info(f"成功加载 {len(self.examples)} 条训练样本")
            
        except Exception as e:
            logging.error(f"加载数据文件失败: {str(e)}")
            raise
    
    def _construct_training_text(self, item: Dict[str, Any]) -> Optional[str]:
        """构建训练文本"""
        try:
            # 构建结构化的训练文本
            text_parts = []
            
            # 添加标题
            if item.get('title'):
                text_parts.append(f"标题：{item['title']}")
            
            # 添加内容
            if item.get('content'):
                text_parts.append(f"内容：{item['content']}")
            
            # 添加来源信息
            if item.get('source'):
                text_parts.append(f"来源：{item['source']}")
            
            # 添加类型信息
            if item.get('type'):
                text_parts.append(f"类型：{item['type']}")
            
            return '\n'.join(text_parts) if text_parts else None
            
        except Exception as e:
            logging.error(f"构建训练文本时出错: {str(e)}")
            return None
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        return self.examples[idx]

class LoRATrainer:
    """LoRA 训练器"""
    
    def __init__(self, config):
        self.config = config
        self._setup_logging()
        
        # 检查可用的 GPU
        self.num_gpus = torch.cuda.device_count()
        if self.num_gpus > 1:
            self.logger.info(f"检测到 {self.num_gpus} 张 GPU 卡将使用分布式训练")
        else:
            self.logger.info("使用单 GPU 训练")
            
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 初始化分词器和模型
        self.tokenizer = None
        self.model = None
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config.STORAGE_PATHS["logs"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"lora_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("LoRATrainer")
    
    def prepare_model(self):
        """准备模型"""
        try:
            self.logger.info("开始加载基础模型和分词器...")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.BASE_MODEL_NAME,
                trust_remote_code=True
            )
            
            # 加载模型
            from transformers import AutoModelForCausalLM
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.BASE_MODEL_NAME,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
                device_map=None,  # 不使用自动设备映射
                low_cpu_mem_usage=True
            )
            
            # 配置 LoRA
            peft_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=self.config.LORA_CONFIG["r"],
                lora_alpha=self.config.LORA_CONFIG["lora_alpha"],
                lora_dropout=self.config.LORA_CONFIG["lora_dropout"],
                target_modules=self.config.LORA_CONFIG["target_modules"],
                bias=self.config.LORA_CONFIG.get("bias", "none")
            )
            
            # 准备模型进行训练
            self.model = prepare_model_for_kbit_training(self.model)
            
            # 将模型转换为 LoRA 模型
            self.model = get_peft_model(self.model, peft_config)
            
            # 将模型移动到 GPU
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            
            self.logger.info("模型准备完成")
            
        except Exception as e:
            self.logger.error(f"准备模型时出错: {str(e)}")
            raise
    
    def train(self, train_data_path: str, eval_data_path: Optional[str] = None):
        """训练模型"""
        try:
            self.logger.info("开始训练准备...")
            
            # 加载训练数据
            train_dataset = self.load_dataset(train_data_path)
            
            # 设置基本训练参数
            training_args = TrainingArguments(
                output_dir=self.config.TRAINING_CONFIG["output_dir"],
                num_train_epochs=self.config.TRAINING_CONFIG["num_train_epochs"],
                per_device_train_batch_size=self.config.TRAINING_CONFIG["per_device_train_batch_size"],
                learning_rate=self.config.TRAINING_CONFIG["learning_rate"],
                save_steps=self.config.TRAINING_CONFIG["save_steps"],
                logging_steps=self.config.TRAINING_CONFIG["logging_steps"],
                save_total_limit=self.config.TRAINING_CONFIG["save_total_limit"],
                remove_unused_columns=False,
                fp16=False,
                bf16=True,
                gradient_checkpointing=True,
                gradient_accumulation_steps=8,  # 增加梯度累积步数
                warmup_steps=100,
                max_grad_norm=0.3,
                optim="adamw_torch"
            )
            
            # 创建数据整理器
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
            
            # 创建训练器
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                data_collator=data_collator
            )
            
            self.logger.info("开始训练...")
            trainer.train()
            
            # 保存模型
            output_dir = os.path.join(self.config.STORAGE_PATHS["model_cache"], "lora_final")
            trainer.save_model(output_dir)
            self.tokenizer.save_pretrained(output_dir)
            self.logger.info(f"训练完成，模型已保存到: {output_dir}")
            
        except Exception as e:
            self.logger.error(f"训练过程出错: {str(e)}")
            raise
    
    def evaluate(self, test_data_path: str):
        """评估模型"""
        try:
            self.logger.info("开始评估模型...")
            
            # 加载测试数据
            test_dataset = MedicalDataset(
                test_data_path,
                self.tokenizer,
                max_length=128  # 固定最大长度
            )
            
            # 设置评估参数
            eval_args = TrainingArguments(
                output_dir=os.path.join(self.config.STORAGE_PATHS["model_cache"], "eval_results"),
                per_device_eval_batch_size=self.config.TRAINING_CONFIG["batch_size"],
                remove_unused_columns=False
            )
            
            # 创建评估器
            evaluator = Trainer(
                model=self.model,
                args=eval_args,
                eval_dataset=test_dataset
            )
            
            # 进行评估
            metrics = evaluator.evaluate()
            
            # 保存评估结果
            results_dir = Path(self.config.STORAGE_PATHS["output"]) / "evaluation_results"
            results_dir.mkdir(parents=True, exist_ok=True)
            
            results_file = results_dir / f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"评估完成，结果已保存到: {results_file}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"评估过程出错: {str(e)}", exc_info=True)
            raise 
    
    def load_dataset(self, data_path: str) -> MedicalDataset:
        """加载数据集"""
        try:
            # 检查文件是否存在
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"数据文件不存在: {data_path}")
                
            # 加载数据集
            dataset = MedicalDataset(
                data_path=data_path,
                tokenizer=self.tokenizer,
                max_length=128  # 固定最大长度
            )
            
            self.logger.info(f"成功加载数据集，共 {len(dataset)} 条记录")
            return dataset
            
        except Exception as e:
            self.logger.error(f"加载数据集失败: {str(e)}")
            raise 