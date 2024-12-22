import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class MedicalCrawler:
    def __init__(self, config):
        self.config = config
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = None
        
    async def initialize(self):
        """初始化异步会话"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            
    async def crawl_nih(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """从 NIH 爬取医疗数据"""
        results = []
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        headers = self.config.CRAWLER_CONFIG["headers"]
        
        for keyword in keywords:
            try:
                # 使用 E-utilities API 搜索
                search_url = f"{base_url}/esearch.fcgi?db=pubmed&term={quote(keyword)}&retmode=json&retmax=10"
                print(f"正在爬取 NIH E-utilities: {search_url}")
                
                async with self.session.get(search_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            id_list = data.get('esearchresult', {}).get('idlist', [])
                            print(f"找到 {len(id_list)} 篇文章")
                            
                            if id_list:
                                # 获取文章详情
                                ids = ','.join(id_list)
                                summary_url = f"{base_url}/efetch.fcgi?db=pubmed&id={ids}&retmode=xml"
                                
                                async with self.session.get(summary_url, headers=headers) as summary_response:
                                    if summary_response.status == 200:
                                        xml_content = await summary_response.text()
                                        soup = BeautifulSoup(xml_content, 'xml')
                                        articles = soup.find_all('PubmedArticle')
                                        
                                        for article in articles:
                                            try:
                                                # 提取文章ID
                                                article_id = article.find('PMID').text if article.find('PMID') else None
                                                
                                                if article_id:
                                                    # 提取标题
                                                    title = article.find('ArticleTitle')
                                                    title_text = title.text if title else ''
                                                    
                                                    # 提取摘要
                                                    abstract = article.find('Abstract')
                                                    abstract_text = abstract.text if abstract else ''
                                                    
                                                    # 提取作者
                                                    authors = []
                                                    author_list = article.find('AuthorList')
                                                    if author_list:
                                                        for author in author_list.find_all('Author'):
                                                            last_name = author.find('LastName')
                                                            fore_name = author.find('ForeName')
                                                            if last_name and fore_name:
                                                                authors.append(f"{fore_name.text} {last_name.text}")
                                                            elif last_name:
                                                                authors.append(last_name.text)
                                                    
                                                    # 提取发布日期
                                                    pub_date = article.find('PubDate')
                                                    year = pub_date.find('Year').text if pub_date and pub_date.find('Year') else ''
                                                    month = pub_date.find('Month').text if pub_date and pub_date.find('Month') else ''
                                                    day = pub_date.find('Day').text if pub_date and pub_date.find('Day') else ''
                                                    publication_date = f"{year} {month} {day}".strip()
                                                    
                                                    data = {
                                                        'title': title_text,
                                                        'content': abstract_text,
                                                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/",
                                                        'source': 'NIH PubMed',
                                                        'source_info': ', '.join(authors) if authors else 'Unknown',
                                                        'keyword': keyword,
                                                        'crawl_time': datetime.now().isoformat(),
                                                        'publication_date': publication_date
                                                    }
                                                    
                                                    results.append(data)
                                                    print(f"已爬取文章: {data['title'][:50]}...")
                                                    
                                            except Exception as e:
                                                print(f"处理文章时出错: {str(e)}")
                                                print(f"错误类型: {type(e)}")
                                                continue
                                    else:
                                        print(f"获取文章详情失败，状态码: {summary_response.status}")
                                        
                        except Exception as e:
                            print(f"解析响应失败: {str(e)}")
                            print(f"错误类型: {type(e)}")
                            
                    else:
                        print(f"请求失败，状态码: {response.status}")
                        print(await response.text())
                        
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取 NIH 关键词 {keyword} 失败: {str(e)}")
                print(f"错误类型: {type(e)}")
                import traceback
                print(f"错误堆栈: {traceback.format_exc()}")
                continue
                
        return results
        
    async def crawl_pubmed(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """从 PubMed 爬取医学文献"""
        results = []
        base_url = self.config.CRAWLER_CONFIG["pubmed_base_url"]
        
        for keyword in keywords:
            try:
                # 使用英文关键词构建URL
                search_url = f"{base_url}/?term={quote(keyword.replace(' ', '+'))}"
                print(f"正在爬取 PubMed: {search_url}")
                
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 提取搜索结果
                        articles = soup.find_all('article', class_='full-docsum')
                        print(f"找到 {len(articles)} 篇文献")
                        
                        for article in articles:
                            try:
                                title_elem = article.find('a', class_='docsum-title')
                                abstract_elem = article.find('div', class_='full-view-snippet')
                                authors_elem = article.find('span', class_='docsum-authors')
                                
                                if title_elem:
                                    data = {
                                        'title': title_elem.text.strip(),
                                        'abstract': abstract_elem.text.strip() if abstract_elem else "",
                                        'authors': authors_elem.text.strip() if authors_elem else "",
                                        'url': base_url + title_elem['href'] if title_elem.has_attr('href') else "",
                                        'source': 'PubMed',
                                        'keyword': keyword,
                                        'crawl_time': datetime.now().isoformat()
                                    }
                                    results.append(data)
                                    
                            except Exception as e:
                                print(f"处理文献时出错: {str(e)}")
                                continue
                                
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取 PubMed 关键词 {keyword} 失败: {str(e)}")
                continue
                
        return results
        
    async def crawl_who(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """从世界卫生组织网站爬取数据"""
        results = []
        base_url = "https://www.who.int/publications/i/search"
        
        for keyword in keywords:
            try:
                search_url = f"{base_url}?query={quote(keyword)}"
                print(f"正在爬取 WHO: {search_url}")
                
                async with self.session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        articles = soup.find_all('div', class_='search-results__item')
                        print(f"找到 {len(articles)} 篇文章")
                        
                        for article in articles:
                            try:
                                title = article.find('h3', class_='search-results__item-title')
                                abstract = article.find('div', class_='search-results__item-description')
                                date = article.find('div', class_='search-results__item-date')
                                
                                if title:
                                    data = {
                                        'title': title.text.strip(),
                                        'content': abstract.text.strip() if abstract else "",
                                        'url': "https://www.who.int" + title.find('a')['href'] if title.find('a') else "",
                                        'source': 'WHO',
                                        'keyword': keyword,
                                        'crawl_time': datetime.now().isoformat(),
                                        'publication_date': date.text.strip() if date else ""
                                    }
                                    results.append(data)
                                    
                            except Exception as e:
                                print(f"处理 WHO 文章时出错: {str(e)}")
                                continue
                                
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取 WHO 关键词 {keyword} 失败: {str(e)}")
                continue
                
        return results
        
    async def crawl_cdc(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """从疾病控制中心网站爬取数据"""
        results = []
        base_url = "https://www.cdc.gov/search"
        
        for keyword in keywords:
            try:
                search_url = f"{base_url}/?query={quote(keyword)}"
                print(f"正在爬取 CDC: {search_url}")
                
                async with self.session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        articles = soup.find_all('div', class_='searchResults')
                        print(f"找到 {len(articles)} 篇文章")
                        
                        for article in articles:
                            try:
                                title = article.find('h3', class_='item-title')
                                summary = article.find('div', class_='item-description')
                                
                                if title:
                                    data = {
                                        'title': title.text.strip(),
                                        'content': summary.text.strip() if summary else "",
                                        'url': "https://www.cdc.gov" + title.find('a')['href'] if title.find('a') else "",
                                        'source': 'CDC',
                                        'keyword': keyword,
                                        'crawl_time': datetime.now().isoformat()
                                    }
                                    results.append(data)
                                    
                            except Exception as e:
                                print(f"处理 CDC 文章时出错: {str(e)}")
                                continue
                                
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取 CDC 关键词 {keyword} 失败: {str(e)}")
                continue
                
        return results
        
    async def crawl_medical_books(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """爬取专业医疗健康书籍信息"""
        results = []
        base_url = "https://www.ncbi.nlm.nih.gov/books"
        
        for keyword in keywords:
            try:
                search_url = f"{base_url}/search?term={quote(keyword)}"
                print(f"正在爬取医学书籍: {search_url}")
                
                async with self.session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        books = soup.find_all('div', class_='rslt')
                        print(f"找到 {len(books)} 本相关书籍")
                        
                        for book in books:
                            try:
                                title = book.find('a', class_='title')
                                authors = book.find('div', class_='authors')
                                summary = book.find('div', class_='desc')
                                
                                if title:
                                    data = {
                                        'title': title.text.strip(),
                                        'authors': authors.text.strip() if authors else "",
                                        'summary': summary.text.strip() if summary else "",
                                        'url': "https://www.ncbi.nlm.nih.gov" + title['href'] if title.has_attr('href') else "",
                                        'source': 'Medical Books',
                                        'type': 'book',
                                        'keyword': keyword,
                                        'crawl_time': datetime.now().isoformat()
                                    }
                                    results.append(data)
                                    
                            except Exception as e:
                                print(f"处理书籍数据时出错: {str(e)}")
                                continue
                                
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取医学书籍关键词 {keyword} 失败: {str(e)}")
                continue
                
        return results
        
    async def crawl_medical_guidelines(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """爬取诊疗指南和案例"""
        results = []
        base_url = "https://www.guidelines.gov/search"
        
        for keyword in keywords:
            try:
                search_url = f"{base_url}?term={quote(keyword)}"
                print(f"正在爬取诊疗指南: {search_url}")
                
                async with self.session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        guidelines = soup.find_all('div', class_='guideline-item')
                        print(f"找到 {len(guidelines)} 条诊疗指南")
                        
                        for guideline in guidelines:
                            try:
                                title = guideline.find('h3', class_='guideline-title')
                                org = guideline.find('div', class_='organization')
                                content = guideline.find('div', class_='guideline-content')
                                
                                if title:
                                    data = {
                                        'title': title.text.strip(),
                                        'organization': org.text.strip() if org else "",
                                        'content': content.text.strip() if content else "",
                                        'url': title.find('a')['href'] if title.find('a') else "",
                                        'source': 'Medical Guidelines',
                                        'type': 'guideline',
                                        'keyword': keyword,
                                        'crawl_time': datetime.now().isoformat()
                                    }
                                    results.append(data)
                                    
                            except Exception as e:
                                print(f"处理指南数据时出错: {str(e)}")
                                continue
                                
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取诊疗指南关键词 {keyword} 失败: {str(e)}")
                continue
                
        return results
        
    async def crawl_medical_wiki(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """爬取医学百科词条"""
        results = []
        base_url = "https://medlineplus.gov/encyclopedia.html"
        
        for keyword in keywords:
            try:
                search_url = f"{base_url}?search={quote(keyword)}"
                print(f"正在爬取医学百科: {search_url}")
                
                async with self.session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        articles = soup.find_all('div', class_='encyclopedia-item')
                        print(f"找到 {len(articles)} 条百科词条")
                        
                        for article in articles:
                            try:
                                title = article.find('h2', class_='title')
                                content = article.find('div', class_='content')
                                
                                if title:
                                    data = {
                                        'title': title.text.strip(),
                                        'content': content.text.strip() if content else "",
                                        'url': title.find('a')['href'] if title.find('a') else "",
                                        'source': 'Medical Encyclopedia',
                                        'type': 'wiki',
                                        'keyword': keyword,
                                        'crawl_time': datetime.now().isoformat()
                                    }
                                    results.append(data)
                                    
                            except Exception as e:
                                print(f"处理百科数据时出错: {str(e)}")
                                continue
                                
                await asyncio.sleep(self.config.CRAWLER_CONFIG["delay"])
                
            except Exception as e:
                print(f"爬取医学百科关键词 {keyword} 失败: {str(e)}")
                continue
                
        return results
        
    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """保存爬取结果"""
        save_path = self.config.STORAGE_PATHS["raw_data"] / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
    async def run_crawler(self, keywords: List[str]):
        """运行爬虫"""
        try:
            await self.initialize()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 并行爬取所有数据源
            tasks = [
                self.crawl_nih(keywords),
                self.crawl_pubmed(keywords),
                self.crawl_who(keywords),
                self.crawl_cdc(keywords),
                self.crawl_medical_books(keywords),
                self.crawl_medical_guidelines(keywords),
                self.crawl_medical_wiki(keywords)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 保存结果
            sources = ['nih', 'pubmed', 'who', 'cdc', 'books', 'guidelines', 'wiki']
            for source, data in zip(sources, results):
                if data:
                    self.save_results(data, f'{source}_{timestamp}.jsonl')
            
            # 打印统计信息
            print("\n爬取统计:")
            for source, data in zip(sources, results):
                print(f"{source.upper()}: 获取 {len(data)} 条记录")
            
        finally:
            await self.close() 