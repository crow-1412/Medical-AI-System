###安装所需依赖
pip install gradio transformers torch bitsandbytes accelerate sentence-transformers faiss-cpu langchain-community beautifulsoup4 python-dotenv sentencepiece
### 配置 Git
git config --global user.name "您的用户名"
git config --global user.email "您的邮箱"
### 设置远程仓库 URL（替换 YOUR_TOKEN 为您的 GitHub token）
git remote set-url origin https://YOUR_TOKEN@github.com/crow-1412/Medical-AI-System.git
### 运行知识库初始化脚本
python scripts/init_knowledge_base.py
### 访问方式
#### 本地访问
打开浏览器访问：http://localhost:7860
# 运行主程序
python interface/gradio_app.py
# 克隆仓库
git clone https://github.com/crow-1412/Medical-AI-System.git
# 提交更新
git add .
git commit -m "更新说明"
git push origin main
## 基于多智能体架构的智能系统搭建
#### 作业描述：选择一个目标行业，比如，司法、医疗、金融等，以多智能体的形式，建构智能化流程，设计一款 AI 系统。
![image](https://github.com/user-attachments/assets/ae1232a6-993a-4970-8bab-6ba3fdb7b02d)
![image](https://github.com/user-attachments/assets/b223e954-ca69-4088-b1a7-25bce909350f)
