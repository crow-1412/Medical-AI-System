#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
医疗数据爬虫主程序
"""

import asyncio
import logging
from crawlers.medical_crawler import MedicalCrawler
from config.config import Config

async def main():
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 初始化配置
    config = Config()
    
    # 创建爬虫实例
    crawler = MedicalCrawler()
    
    try:
        # 中文关键词列表
        keywords_zh = ['高血压', '糖尿病', '冠心病', '脑卒中', '慢性肾病', '癌症', '肺炎', '哮喘', '关节炎', '抑郁症']
        # 英文关键词列表
        keywords_en = ['hypertension', 'diabetes', 'coronary heart disease', 'stroke', 'chronic kidney disease', 
                      'cancer', 'pneumonia', 'asthma', 'arthritis', 'depression']
        
        # 使用英文关键词爬取国际资源
        print("\n使用英文关键词爬取国际资源...")
        for keyword in keywords_en:
            logger.info(f"正在爬取关键词: {keyword}")
            await crawler.run_crawler(keyword)
            # 添加延迟避免请求过于频繁
            await asyncio.sleep(5)
        
        # 使用中文关键词爬取中文资源
        print("\n使用中文关键词爬取中文资源...")
        for keyword in keywords_zh:
            logger.info(f"正在爬取关键词: {keyword}")
            # 只使用中文数据源
            tasks = [
                crawler.crawl_wanfang(keyword),
                crawler.crawl_vip(keyword),
                crawler.crawl_sinomed(keyword)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for source, result in zip(['万方', '维普', '中国生物医学'], results):
                if isinstance(result, Exception):
                    logger.error(f"{source}爬取失败: {str(result)}")
                else:
                    logger.info(f"{source}爬取成功，获取 {len(result)} 条记录")
            
            # 添加延迟避免请求过于频繁
            await asyncio.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭爬虫...")
    except Exception as e:
        logger.error(f"爬虫运行出错: {str(e)}")
    finally:
        # 关闭爬虫会话
        await crawler.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已被用户中断") 