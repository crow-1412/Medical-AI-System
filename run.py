import asyncio
import logging
from pathlib import Path
from config.config import Config
from crawlers.medical_crawler import MedicalCrawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

async def main():
    # 医学关键词列表
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
        }
    ]  # 可以根据需要添加更多关键词
    
    try:
        # 初始化爬虫
        crawler = MedicalCrawler(Config)
        logging.info(f"开始爬取数据，关键词：{[k['zh'] for k in keywords]}")
        
        # 使用英文关键词爬取
        en_keywords = [k['en'] for k in keywords]
        await crawler.run_crawler(en_keywords)
        
        # 检查结果
        raw_data_path = Config.STORAGE_PATHS["raw_data"]
        files = list(raw_data_path.glob("*.jsonl"))
        
        logging.info("\n爬取结果：")
        total_records = 0
        for file in files:
            line_count = sum(1 for _ in open(file, 'r', encoding='utf-8'))
            total_records += line_count
            logging.info(f"{file.name}: {line_count} 条记录")
            
        logging.info(f"总计爬取: {total_records} 条记录")
        
    except Exception as e:
        logging.error(f"爬虫运行出错: {str(e)}", exc_info=True)
        raise e

if __name__ == "__main__":
    asyncio.run(main()) 