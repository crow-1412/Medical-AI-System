from transformers import Trainer, TrainingArguments, AutoModelForCausalLM, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType
import torch
import logging
from pathlib import Path
from datasets import Dataset

logger = logging.getLogger(__name__)

class LoRATrainer:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.peft_config = None
        # 初始化时加载模型和分词器
        self._load_base_model()
        
    def _load_base_model(self):
        """加载基础模型和分词器"""
        try:
            local_model_path = "/root/autodl-tmp/model_cache/models--baichuan-inc--Baichuan2-7B-Chat/snapshots/ea66ced17780ca3db39bc9f8aa601d8463db3da5"
            logger.info(f"从本地加载模型: {local_model_path}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                local_model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # 确保有 pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                local_model_path,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.float16,
                local_files_only=True,
                load_in_8bit=True
            )
            
            # 设置为训练模式
            self.model.train()
            
            # 配置 LoRA
            self.setup_lora(self.model)
            
            logger.info("基础模型加载完成")
            
        except Exception as e:
            logger.error(f"加载基础模型失败: {str(e)}")
            raise
        
    def setup_lora(self, model):
        """配置 LoRA"""
        try:
            self.peft_config = LoraConfig(
                r=self.config.LORA_CONFIG["r"],
                lora_alpha=self.config.LORA_CONFIG["lora_alpha"],
                target_modules=self.config.LORA_CONFIG["target_modules"],
                lora_dropout=self.config.LORA_CONFIG["lora_dropout"],
                bias=self.config.LORA_CONFIG["bias"],
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                modules_to_save=None
            )
            
            # 获取 PEFT 模型
            self.model = get_peft_model(model, self.peft_config)
            
            # 打印可训练参数信息
            self.model.print_trainable_parameters()
            
        except Exception as e:
            logger.error(f"配置 LoRA 失败: {str(e)}")
            raise
        
    def _prepare_dataset(self, data):
        """准备训练数据集"""
        try:
            # 转换为 HuggingFace Dataset 格式
            dataset = Dataset.from_dict({
                "text": [item["text"] for item in data]
            })
            
            # 对数据进行编码
            def tokenize_function(examples):
                # 使用分词器处理文本
                outputs = self.tokenizer(
                    examples["text"],
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                    return_tensors=None  # 确保返回列表而不是张量
                )
                
                # 创建标签，用于计算损失
                outputs["labels"] = outputs["input_ids"].copy()
                
                return outputs
            
            # 处理数据集
            tokenized_dataset = dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=dataset.column_names
            )
            
            return tokenized_dataset
            
        except Exception as e:
            logger.error(f"准备数据集失败: {str(e)}")
            raise
        
    def _collate_fn(self, examples):
        """数据批处理函数"""
        batch = {
            "input_ids": torch.tensor([ex["input_ids"] for ex in examples]),
            "attention_mask": torch.tensor([ex["attention_mask"] for ex in examples]),
            "labels": torch.tensor([ex["labels"] for ex in examples])  # 添加标签
        }
        return batch
        
    def train(self, train_dataset, **kwargs):
        """训练模型"""
        try:
            # 设置训练参数
            training_args = TrainingArguments(
                output_dir=kwargs.get('output_dir', self.config.STORAGE_ROOT / "lora_weights"),
                num_train_epochs=self.config.TRAINING_CONFIG["num_epochs"],
                per_device_train_batch_size=self.config.TRAINING_CONFIG["batch_size"],
                gradient_accumulation_steps=self.config.TRAINING_CONFIG["gradient_accumulation_steps"],
                learning_rate=self.config.TRAINING_CONFIG["learning_rate"],
                weight_decay=self.config.TRAINING_CONFIG["weight_decay"],
                warmup_steps=self.config.TRAINING_CONFIG["warmup_steps"],
                max_grad_norm=self.config.TRAINING_CONFIG["max_grad_norm"],
                logging_steps=self.config.TRAINING_CONFIG["logging_steps"],
                save_steps=self.config.TRAINING_CONFIG["save_steps"],
                save_strategy="steps",
                fp16=self.config.TRAINING_CONFIG["fp16"],
                logging_dir=self.config.STORAGE_ROOT / "logs",
                report_to="tensorboard",
                remove_unused_columns=False,
                prediction_loss_only=True,
                label_names=["labels"]
            )
            
            # 准备数据集
            dataset = self._prepare_dataset(train_dataset)
            
            # 创建训练器
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=dataset,
                data_collator=self._collate_fn,
                tokenizer=self.tokenizer
            )
            
            # 开始训练
            trainer.train()
            
            # 保存模型
            trainer.save_model()
            
        except Exception as e:
            logger.error(f"训练失败: {str(e)}")
            raise
        
    def save_model(self, output_dir: Path):
        """保存模型"""
        self.model.save_pretrained(output_dir) 