"""配置文件"""

import os
from pathlib import Path
import torch

class Config:
    """配置类"""
    
    # 基础模型名称
    BASE_MODEL_NAME = "THUDM/chatglm3-6b"
    
    # 存储路径配置
    STORAGE_PATHS = {
        "raw_data": Path("data/raw"),  # 原始数据目录
        "processed_data": Path("data/processed"),  # 处理后的数据目录
        "model_cache": Path("models"),  # 模型缓存目录
        "output": Path("output"),  # 输出目录
        "logs": Path("logs")  # 日志目录
    }
    
    # 模型配置
    MODEL_CONFIG = {
        "trust_remote_code": True,
        "torch_dtype": torch.bfloat16,
        "low_cpu_mem_usage": True,
        "device_map": "auto"
    }
    
    # LoRA 配置
    LORA_CONFIG = {
        "r": 8,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "target_modules": ["query_key_value"],
        "bias": "none"
    }
    
    # 训练配置
    TRAINING_CONFIG = {
        "output_dir": str(Path("models/lora_checkpoints")),
        "num_train_epochs": 3,
        "per_device_train_batch_size": 1,
        "learning_rate": 2e-4,
        "logging_steps": 10,
        "save_steps": 100,
        "save_total_limit": 3,
        "gradient_accumulation_steps": 4,
        "warmup_steps": 100,
        "max_grad_norm": 0.3
    }
    
    # 知识库配置
    KNOWLEDGE_BASE_CONFIG = {
        "embedding_model": "text2vec-base",  # 向量化模型
        "embedding_dimension": 100,  # 向量维度
        "distance_metric": "cosine",  # 距离度量方式
        "top_k": 5  # 检索时返回的最相似条目数
    }
    
    # 爬虫配置
    CRAWLER_CONFIG = {
        "delay": 5,  # 请求延迟（秒）
        "timeout": 60,  # 请求超时（秒）
        "max_retries": 5,  # 最大重试次数
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1"
        },
        "proxies": [],  # 代理表
        "validation": {
            "required_fields": ["title", "content"],
            "min_content_length": 100,
            "max_content_length": 100000,
            "max_title_length": 200
        },
        # 数据源URL配置
        "urls": {
            "nih_base_url": "https://search.nih.gov/search",
            "pubmed_base_url": "https://pubmed.ncbi.nlm.nih.gov",
            "who_base_url": "https://www.who.int/publications/i/search",
            "cdc_base_url": "https://search.cdc.gov/search",
            "cnki_base_url": "https://kns.cnki.net/kns8/defaultresult/index",
            "medline_base_url": "https://medlineplus.gov/encyclopedia.html",
            "guidelines_base_url": "https://www.guidelines.gov/search"
        },
        # 请求参数配置
        "params": {
            "nih": {
                "affiliate": "nih",
                "query": ""
            },
            "pubmed": {
                "term": ""
            },
            "who": {
                "query": "",
                "page": "1",
                "pagesize": "10",
                "sortBy": "relevance"
            },
            "cdc": {
                "affiliate": "cdc-main",
                "query": ""
            },
            "cnki": {
                "kw": "",
                "crossdb": "1"
            }
        }
    }
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def init_dirs(self):
        """初始化目录"""
        for path in self.STORAGE_PATHS.values():
            path.mkdir(parents=True, exist_ok=True)