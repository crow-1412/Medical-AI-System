from abc import ABC, abstractmethod
from typing import Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
from pathlib import Path
import gc

class BaseAgent(ABC):
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.cache_dir = Path("/root/autodl-tmp/model_cache")
        
    def clean_gpu_memory(self):
        """清理 GPU 内存"""
        if torch.cuda.is_available():
            with torch.cuda.device('cuda'):
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        gc.collect()
    
    def load_model(self):
        """加载模型和分词器"""
        if self.model is None:
            try:
                print(f"从缓存加载模型: {self.model_path}")
                self.clean_gpu_memory()
                
                # 配置 8-bit 量化
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                
                # 设置设备映射，启用多 GPU
                max_memory = {
                    0: "20GB",    # GPU 0 使用 20GB
                    1: "20GB",    # GPU 1 使用 20GB
                    "cpu": "30GB" # CPU 内存
                }
                
                # 加载分词器
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    use_fast=True,
                    cache_dir=self.cache_dir,
                    local_files_only=True
                )
                
                # 加载模型并自动分配到多个 GPU
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    quantization_config=quantization_config,
                    device_map="auto",  # 自动在多GPU间分配
                    max_memory=max_memory,
                    offload_folder="/root/autodl-tmp/offload",
                    cache_dir=self.cache_dir,
                    local_files_only=True,
                    low_cpu_mem_usage=True,
                    use_auth_token=False
                )
                
                # 确保有 pad_token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                # 启用梯度检查点以节省内存
                if hasattr(self.model, "gradient_checkpointing_enable"):
                    self.model.gradient_checkpointing_enable()
                
                # 配置生成参数
                if hasattr(self.model, "config"):
                    self.model.config.use_cache = True
                    
                print("模型加载完成！")
                self.clean_gpu_memory()
                    
            except Exception as e:
                print(f"模型加载失败: {str(e)}")
                import traceback
                print(f"错误堆栈: {traceback.format_exc()}")
                self.clean_gpu_memory()
                raise e
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据的抽象方法，必须由子类实现"""
        pass