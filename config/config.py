import sys
sys.setrecursionlimit(3000)  # 设置更大的递归限制

from pathlib import Path
from typing import Dict
import os
from dotenv import load_dotenv
import torch
from peft import TaskType

load_dotenv()

class Config:
    # 基础配置
    BASE_DIR = Path(__file__).parent.parent
    CACHE_DIR = Path("/root/autodl-tmp/model_cache")
    
    # 设置环境变量
    os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)
    
    # API密钥
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 向量数据库配置
    VECTOR_DB_PATH = Path("/root/autodl-tmp/medical_ai_system/vector_store")
    
    # 模型配置
    BASE_MODEL_NAME = "/root/autodl-tmp/model_cache/models--baichuan-inc--Baichuan2-7B-Chat/snapshots/ea66ced17780ca3db39bc9f8aa601d8463db3da5"
    MODEL_CONFIG = {
        "model_name": BASE_MODEL_NAME,
        "max_memory": {
            0: "20GB",  # GPU 0 使用 20GB
            1: "20GB",  # GPU 1 使用 20GB
            "cpu": "30GB"  # CPU 内存
        },
        "device_map": "auto",  # 自动在多GPU间分配模型层
        "offload_folder": "/root/autodl-tmp/offload",
        "torch_dtype": torch.float16,
        "low_cpu_mem_usage": True,
        "load_in_8bit": True,
        "use_cache": True,
        "max_length": 512,
        "chunk_size": 256,
        "trust_remote_code": True
    }
    
    # LoRA配置
    LORA_CONFIG = {
        "r": 8,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "bias": "none",
        "task_type": TaskType.CAUSAL_LM,
        "target_modules": [
            "W_pack",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ]
    }
    
    # 训练配置
    TRAINING_CONFIG = {
        "batch_size": 2,  # 减小批次大小以适应显存
        "learning_rate": 1e-4,  # 调整学习率
        "num_epochs": 3,
        "weight_decay": 0.01,
        "warmup_steps": 100,
        "max_length": 512,
        "gradient_accumulation_steps": 8,  # 增加梯度累积步数
        "fp16": True,  # 使用混合精度训练
        "logging_steps": 10,
        "save_steps": 100,
        "max_grad_norm": 0.5  # 添加梯度裁剪
    }
    
    # 知识库配置
    KNOWLEDGE_BASE_CONFIG = {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "top_k": 5,
        "similarity_threshold": 0.7,
        "storage_path": BASE_DIR / "storage",
        "vector_dim": 768,  # 向量维度
        "max_tokens": 2048  # 每个文档的最大token数
    }
    
    # 爬虫配置
    CRAWLER_CONFIG = {
        "nih_base_url": "https://www.nih.gov",
        "pubmed_base_url": "https://pubmed.ncbi.nlm.nih.gov",
        "max_retries": 3,
        "timeout": 30,
        "delay": 2.0,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.nih.gov/",
            "DNT": "1"
        }
    }
    
    # 存储路径配置
    STORAGE_ROOT = Path("/root/autodl-tmp/medical_ai_system")
    STORAGE_PATHS = {
        "diseases": STORAGE_ROOT / "diseases.jsonl",
        "templates": STORAGE_ROOT / "templates",
        "embeddings": STORAGE_ROOT / "embeddings",
        "raw_data": STORAGE_ROOT / "raw_data"
    }