#!/bin/bash

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128"

# 直接运行训练脚本
python scripts/process_and_train.py
