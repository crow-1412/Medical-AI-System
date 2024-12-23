from abc import ABC, abstractmethod
from typing import Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
from pathlib import Path
import gc

class BaseAgent(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {self.device}")
        
    def load_model(self):
        """加载模型和分词器"""
        try:
            print(f"正在加载模型 {self.model_name}...")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # 设置特殊token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,  # 使用半精度
                device_map="auto"  # 自动处理模型并行
            )
            
            # 确保模型在正确的设备上
            self.model.to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            print(f"模型加载完成，使用设备: {self.device}")
            print(f"当前GPU显存使用情况:")
            for i in range(torch.cuda.device_count()):
                print(f"GPU {i}: {torch.cuda.memory_allocated(i) / 1024**2:.2f} MB")
                
        except Exception as e:
            print(f"加载模型时出错: {str(e)}")
            raise
            
    def clean_memory(self):
        """清理GPU内存"""
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                with torch.cuda.device(i):
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
            gc.collect()
            print("GPU内存已清理")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据的抽象方法，必须由子类实现"""
        pass