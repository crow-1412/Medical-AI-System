# 医疗报告生成系统

基于多智能体架构的医疗 AI 系统，能够根据患者信息自动生成规范的医疗报告。

## 系统特点

- 多智能体协作架构
- 知识库自动构建和更新
- 支持多种报告类型生成
- 自动症状分析和诊断建议
- 智能治疗方案推荐
- 基于 LoRA 的模型微调

## 系统要求

- Python 3.8+
- CUDA 支持的 GPU（推荐 16GB+ 显存）
- 至少 32GB 系统内存

## 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/crow-1412/Medical-AI-System.git
cd Medical-AI-System
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

或手动安装所需包：
```bash
pip install gradio transformers torch bitsandbytes accelerate sentence-transformers faiss-cpu langchain-community beautifulsoup4 python-dotenv sentencepiece
```

3. 配置环境
```bash
# 配置 Git
git config --global user.name "您的用户名"
git config --global user.email "您的邮箱"

# 设置远程仓库（替换 YOUR_TOKEN 为您的 GitHub token）
git remote set-url origin https://YOUR_TOKEN@github.com/crow-1412/Medical-AI-System.git
```

## 使用说明

1. 初始化知识库
```bash
python scripts/process_and_train.py
```

2. 启动 Web 界面
```bash
python interface/gradio_app.py
```

3. 访问系统
- 本地访问：http://localhost:7860
- 远程访问：
  1. 在 AutoDL 控制台中找到"开放端口"
  2. 将端口 7860 映射到公网
  3. 使用 AutoDL 提供的访问地址

## 功能特性

### 1. 报告类型
- 初步诊断报告
- 住院记录
- 手术记录

### 2. 智能分析
- 症状识别和分析
- 血压等级判断
- 相关疾病关联
- 治疗方案推荐

### 3. 知识库功能
- 自动文档处理
- 向量化存储
- 相似度检索
- 实时知识更新

### 4. 模型训练
- LoRA 微调支持
- 8-bit 量化优化
- 自动梯度检查点
- 多 GPU 支持

## 开发指南

### 代码结构
```
Medical-AI-System/
├── agents/                 # 智能代理模块
├── config/                 # 配置文件
├── crawlers/              # 数据爬取模块
├── interface/             # Web 界面
├── knowledge_base/        # 知识库管理
├── training/              # 模型训练
└── workflows/             # 工作流管理
```

### 更新代码
```bash
git add .
git commit -m "更新说明"
git push origin main
```

## 系统架构

![系统架构图](https://github.com/user-attachments/assets/ae1232a6-993a-4970-8bab-6ba3fdb7b02d)

## 工作流程

![工作流程图](https://github.com/user-attachments/assets/b223e954-ca69-4088-b1a7-25bce909350f)

## 注意事项

1. 内存管理
   - 使用 `clean_gpu_memory()` 定期清理 GPU 内存
   - 设置合适的批处理大小
   - 启用梯度检查点节省显存

2. 并发处理
   - 使用异步操作处理请求
   - 实现单例模式避免重复初始化
   - 使用锁机制确保并发安全

3. 错误处理
   - 完善的异常捕获和日志记录
   - 优雅的错误恢复机制
   - 用户友好的错误提示

## 许可证

[MIT License](LICENSE)
