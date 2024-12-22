import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from crawlers.medical_crawler import MedicalCrawler
from config.config import Config

async def main():
    # 医学关键词列表（中英文对照）
    keywords = [
        {
            "zh": "高血压",
            "en": "hypertension"
        },
        {
            "zh": "糖尿病",
            "en": "diabetes"
        },
        {
            "zh": "冠心病",
            "en": "coronary heart disease"
        },
        {
            "zh": "脑卒中",
            "en": "stroke"
        },
        {
            "zh": "慢性肾病",
            "en": "chronic kidney disease"
        },
        {
            "zh": "癌症",
            "en": "cancer"
        },
        {
            "zh": "肺炎",
            "en": "pneumonia"
        },
        {
            "zh": "哮喘",
            "en": "asthma"
        },
        {
            "zh": "关节炎",
            "en": "arthritis"
        },
        {
            "zh": "抑郁症",
            "en": "depression"
        }
    ]
    
    try:
        # 确保存储目录存在
        os.makedirs(Config.STORAGE_PATHS["raw_data"], exist_ok=True)
        
        # 初始化爬虫
        crawler = MedicalCrawler(Config)
        print(f"开始爬取数据，关键词：{[k['zh'] for k in keywords]}")
        
        # 使用英文关键词爬取
        en_keywords = [k['en'] for k in keywords]
        await crawler.run_crawler(en_keywords)
        
        # 检查结果
        raw_data_path = Config.STORAGE_PATHS["raw_data"]
        files = list(raw_data_path.glob("*.jsonl"))
        
        print("\n爬取结果：")
        for file in files:
            line_count = sum(1 for _ in open(file, 'r', encoding='utf-8'))
            print(f"{file.name}: {line_count} 条记录")
            
    except Exception as e:
        print(f"爬虫运行出错: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(main()) 