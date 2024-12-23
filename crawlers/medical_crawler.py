import logging
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from config.config import Config
import random
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class MedicalCrawler:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.config = Config()
        self._setup_logging()
        
        # 确保存储目录存在
        Path(self.config.STORAGE_PATHS["raw_data"]).mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """设置日志记录系统"""
        # 创建日志目录
        log_dir = Path(self.config.STORAGE_PATHS["logs"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 设置文件处理器
        log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # 设置控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # 获取logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 清除已存在的处理器
        self.logger.handlers.clear()
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 设置不向上级传递日志
        self.logger.propagate = False

    async def fetch(self, url, method='get', params=None, data=None, headers=None, cookies=None, max_retries=3, retry_delay=5):
        """通用的请求，包含重试机制"""
        if headers is None:
            headers = self.headers.copy()
            
        retries = 0
        while retries < max_retries:
            try:
                # 添加随机延迟避免频繁请求
                delay = random.uniform(retry_delay, retry_delay * 2)
                await asyncio.sleep(delay)
                
                if method.lower() == 'get':
                    async with self.session.get(
                        url, 
                        params=params, 
                        headers=headers, 
                        cookies=cookies,
                        ssl=False, 
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:  # Too Many Requests
                            wait_time = int(response.headers.get('Retry-After', retry_delay * 2))
                            self.logger.warning(f"请求频率过高，等待 {wait_time} 秒后重试")
                            await asyncio.sleep(wait_time)
                            retries += 1
                            continue
                        elif response.status == 503:  # Service Unavailable
                            wait_time = retry_delay * (retries + 1)
                            self.logger.warning(f"服务暂时不可用，等待 {wait_time} 秒后重试")
                            await asyncio.sleep(wait_time)
                            retries += 1
                            continue
                        else:
                            self.logger.warning(f"请求失败，状态码: {response.status}")
                            if retries < max_retries - 1:
                                await asyncio.sleep(retry_delay * (retries + 1))
                                retries += 1
                                continue
                            return None
                elif method.lower() == 'post':
                    if headers.get('Content-Type') == 'application/json':
                        async with self.session.post(
                            url, 
                            params=params,
                            json=data,
                            headers=headers,
                            cookies=cookies,
                            ssl=False,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                return await response.text()
                            elif response.status == 429:  # Too Many Requests
                                wait_time = int(response.headers.get('Retry-After', retry_delay * 2))
                                self.logger.warning(f"请求频率过高，等待 {wait_time} 秒后重试")
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue
                            elif response.status == 503:  # Service Unavailable
                                wait_time = retry_delay * (retries + 1)
                                self.logger.warning(f"服务暂时不可用，等待 {wait_time} 秒后重试")
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue
                            else:
                                self.logger.warning(f"请求失败，状态码: {response.status}")
                                if retries < max_retries - 1:
                                    await asyncio.sleep(retry_delay * (retries + 1))
                                    retries += 1
                                    continue
                                return None
                    else:
                        async with self.session.post(
                            url, 
                            params=params,
                            data=data,
                            headers=headers,
                            cookies=cookies,
                            ssl=False,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                return await response.text()
                            elif response.status == 429:  # Too Many Requests
                                wait_time = int(response.headers.get('Retry-After', retry_delay * 2))
                                self.logger.warning(f"请求频率过高，等待 {wait_time} 秒后重试")
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue
                            elif response.status == 503:  # Service Unavailable
                                wait_time = retry_delay * (retries + 1)
                                self.logger.warning(f"服务暂时不可用，等待 {wait_time} 秒后重试")
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue
                            else:
                                self.logger.warning(f"请求失败，状态码: {response.status}")
                                if retries < max_retries - 1:
                                    await asyncio.sleep(retry_delay * (retries + 1))
                                    retries += 1
                                    continue
                                return None
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"请求超时，第 {retries + 1} 次重试")
                if retries < max_retries - 1:
                    await asyncio.sleep(retry_delay * (retries + 1))
                    retries += 1
                    continue
                return None
            except Exception as e:
                self.logger.error(f"请求出错: {str(e)}")
                if retries < max_retries - 1:
                    await asyncio.sleep(retry_delay * (retries + 1))
                    retries += 1
                    continue
                return None
        
        return None

    async def crawl_nih(self, keyword):
        """爬取NIH数据"""
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pmc",
            "term": keyword,
            "retmode": "json",
            "retmax": 20,
            "sort": "relevance"
        }
        
        self.logger.info(f"正在从NIH搜索关键词: {keyword}")
        content = await self.fetch(url, method='get', params=params)
        
        if content:
            try:
                data = json.loads(content)
                article_ids = data.get('esearchresult', {}).get('idlist', [])
                articles = []
                
                # 获取文章详情
                if article_ids:
                    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    summary_params = {
                        "db": "pmc",
                        "id": ",".join(article_ids),
                        "retmode": "json"
                    }
                    
                    summary_content = await self.fetch(summary_url, method='get', params=summary_params)
                    if summary_content:
                        try:
                            summary_data = json.loads(summary_content)
                            result = summary_data.get('result', {})
                            
                            for article_id in article_ids:
                                try:
                                    article = result.get(article_id, {})
                                    title = article.get('title', '')
                                    link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{article_id}/"
                                    description = article.get('abstract', '')
                                    
                                    articles.append({
                                        'title': title,
                                        'url': link,
                                        'description': description,
                                        'source': 'NIH'
                                    })
                                except Exception as e:
                                    self.logger.error(f"解析NIH文章详情时出错: {str(e)}")
                                    continue
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析NIH文章摘要JSON时出错: {str(e)}")
                
                self.logger.info(f"从NIH获取到 {len(articles)} 篇文章")
                return articles
            except json.JSONDecodeError as e:
                self.logger.error(f"解析NIH搜索结果JSON时出错: {str(e)}")
                return []
        return []

    async def crawl_pubmed(self, keyword):
        """爬取PubMed数据"""
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": keyword,
            "retmode": "json",
            "retmax": 20,
            "sort": "relevance"
        }
        
        self.logger.info(f"正在从PubMed搜索关键词: {keyword}")
        content = await self.fetch(url, method='get', params=params)
        
        if content:
            try:
                data = json.loads(content)
                article_ids = data.get('esearchresult', {}).get('idlist', [])
                articles = []
                
                # 获取文章详情
                if article_ids:
                    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    summary_params = {
                        "db": "pubmed",
                        "id": ",".join(article_ids),
                        "retmode": "json"
                    }
                    
                    summary_content = await self.fetch(summary_url, method='get', params=summary_params)
                    if summary_content:
                        try:
                            summary_data = json.loads(summary_content)
                            result = summary_data.get('result', {})
                            
                            for article_id in article_ids:
                                try:
                                    article = result.get(article_id, {})
                                    title = article.get('title', '')
                                    link = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
                                    description = article.get('abstract', '')
                                    
                                    articles.append({
                                        'title': title,
                                        'url': link,
                                        'description': description,
                                        'source': 'PubMed'
                                    })
                                except Exception as e:
                                    self.logger.error(f"解析PubMed文章详情时出错: {str(e)}")
                                    continue
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析PubMed文章摘要JSON时出错: {str(e)}")
                
                self.logger.info(f"从PubMed获取到 {len(articles)} 篇文章")
                return articles
            except json.JSONDecodeError as e:
                self.logger.error(f"解析PubMed搜索结果JSON时出错: {str(e)}")
                return []
        return []

    async def crawl_who(self, keyword):
        """爬取WHO数据"""
        # 使用多个WHO数据源
        sources = [
            {
                'url': 'https://www.who.int/rss-feeds/news-english.xml',
                'type': 'rss',
                'headers': {
                    **self.headers,
                    'Accept': 'application/rss+xml',
                    'Accept-Language': 'en-US,en;q=0.5'
                }
            },
            {
                'url': 'https://www.who.int/publications/i/search',
                'type': 'html',
                'headers': {
                    **self.headers,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5'
                },
                'params': {
                    'q': keyword,
                    'page': '1',
                    'pagesize': '20',
                    'sort': 'relevance',
                    'language': 'en'
                }
            }
        ]
        
        self.logger.info(f"正在从WHO搜索关键词: {keyword}")
        articles = []
        
        for source in sources:
            try:
                content = await self.fetch(
                    source['url'],
                    method='get',
                    params=source.get('params'),
                    headers=source['headers']
                )
                
                if content:
                    if source['type'] == 'rss':
                        soup = BeautifulSoup(content, 'xml')
                        items = soup.find_all('item')
                        
                        for item in items:
                            try:
                                title = item.title.text if item.title else ''
                                description = item.description.text if item.description else ''
                                link = item.link.text if item.link else ''
                                
                                # 检查标题或描述是否包含关键词
                                if (keyword.lower() in title.lower() or 
                                    keyword.lower() in description.lower()):
                                    articles.append({
                                        'title': title,
                                        'url': link,
                                        'description': description,
                                        'source': 'WHO'
                                    })
                            except Exception as e:
                                self.logger.error(f"解析WHO RSS结果时出错: {str(e)}")
                                continue
                    else:  # html
                        soup = BeautifulSoup(content, 'html.parser')
                        results = soup.find_all('div', class_='sf-item-list')
                        
                        for result in results:
                            try:
                                title_elem = result.find(['h4', 'h3', 'h2'], class_=['sf-item-title', 'title'])
                                if title_elem and (title_elem.a or title_elem.text):
                                    title = title_elem.a.text.strip() if title_elem.a else title_elem.text.strip()
                                    url = title_elem.a['href'] if title_elem.a else ''
                                    if url and not url.startswith('http'):
                                        url = f"https://www.who.int{url}"
                                        
                                    description = ''
                                    desc_elem = result.find('div', class_=['sf-item-description', 'description'])
                                    if desc_elem:
                                        description = desc_elem.text.strip()
                                    
                                    articles.append({
                                        'title': title,
                                        'url': url,
                                        'description': description,
                                        'source': 'WHO'
                                    })
                            except Exception as e:
                                self.logger.error(f"解析WHO HTML结果时出错: {str(e)}")
                                continue
            except Exception as e:
                self.logger.error(f"获取WHO数据源时出错: {str(e)}")
                continue
        
        # 去重
        unique_articles = []
        seen_urls = set()
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        # 只保留前20篇
        unique_articles = unique_articles[:20]
        
        self.logger.info(f"从WHO获取到 {len(unique_articles)} 篇文章")
        return unique_articles

    async def crawl_cnki(self, keyword):
        """爬取CNKI数据"""
        # 使用 CNKI 的学术搜索
        search_url = "https://scholar.cnki.net/home/search"
        headers = {
            **self.headers,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://scholar.cnki.net/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        params = {
            'q': keyword,
            'type': 'all',
            'lang': 'all',
            'page': '1',
            'size': '20',
            'sort': 'relevance'
        }
        
        self.logger.info(f"正在从CNKI搜索关键词: {keyword}")
        
        # 第一步：获取初始页面和 cookie
        init_content = await self.fetch(
            search_url,
            method='get',
            params=params,
            headers=headers
        )
        
        if init_content:
            try:
                soup = BeautifulSoup(init_content, 'html.parser')
                articles = []
                
                # 解析搜索结果
                results = soup.find_all('div', class_='search-result-item')
                
                for result in results:
                    try:
                        title_elem = result.find('h3', class_='title')
                        if title_elem and title_elem.a:
                            title = title_elem.a.text.strip()
                            url = title_elem.a['href']
                            if not url.startswith('http'):
                                url = f"https://scholar.cnki.net{url}"
                                
                            description = ''
                            desc_elem = result.find('div', class_='abstract')
                            if desc_elem:
                                description = desc_elem.text.strip()
                            
                            articles.append({
                                'title': title,
                                'url': url,
                                'description': description,
                                'source': 'CNKI'
                            })
                    except Exception as e:
                        self.logger.error(f"解析CNKI结果时出错: {str(e)}")
                        continue
                
                # 去重
                unique_articles = []
                seen_urls = set()
                for article in articles:
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        unique_articles.append(article)
                
                # 只保留前20篇
                unique_articles = unique_articles[:20]
                
                self.logger.info(f"从CNKI获取到 {len(unique_articles)} 篇文章")
                return unique_articles
            except Exception as e:
                self.logger.error(f"解析CNKI搜索结果时出错: {str(e)}")
                return []
        return []

    async def run_crawler(self, keyword):
        """运行爬虫"""
        try:
            # 创建国际数据源爬虫任务
            tasks = [
                self.crawl_nih(keyword),
                self.crawl_pubmed(keyword),
                self.crawl_who(keyword)
            ]
            
            # 并发执行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            all_results = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 定义数据源名称
            sources = ['nih', 'pubmed', 'who']
            
            # 处理结果
            for source, result in zip(sources, results):
                if isinstance(result, Exception):
                    self.logger.error(f"{source} 爬取失败: {str(result)}")
                    continue
                    
                self.logger.info(f"{source} 爬取成功，获取 {len(result)} 记录")
                
                # 分别保存每个来源的结果
                filename = f"{source}_{keyword}_{timestamp}.json"
                self.save_results(result, filename)
                
                all_results.extend(result)
            
            # 保存所有结果
            filename = f"all_results_{keyword}_{timestamp}.json"
            self.save_results(all_results, filename)
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"爬取关键词 {keyword} 时出错: {str(e)}")
            return []

    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """保存爬取结果"""
        try:
            save_path = Path(self.config.STORAGE_PATHS["raw_data"]) / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件已存在，添加序号
            counter = 1
            while save_path.exists():
                new_filename = f"{save_path.stem}_{counter}{save_path.suffix}"
                save_path = save_path.parent / new_filename
                counter += 1
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"结果已保存: {save_path}")
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {str(e)}")

    async def close(self):
        """关闭爬虫会话"""
        if self.session:
            await self.session.close()
            self.logger.info("爬虫会话已关闭")

class VectorStoreManager:
    def __init__(self, config):
        self.config = config
        # 使用sentence-transformers替代OpenAI embeddings
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.client = chromadb.PersistentClient(
            path=str(self.config.VECTOR_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
        
    def initialize_store(self):
        """初始化向量存储"""
        try:
            self.collection = self.client.get_or_create_collection(
                name="medical_knowledge",
                metadata={"description": "医疗知识库"}
            )
        except Exception as e:
            print(f"初始化向量存储失败: {str(e)}")
            raise
        
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            if not self.collection:
                self.initialize_store()
            
            # 生成查询向量
            query_embedding = self.model.encode(query)
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k
            )
            
            # 格式化结果
            documents = []
            for idx, (doc, score) in enumerate(zip(results['documents'][0], results['distances'][0])):
                documents.append({
                    'content': doc,
                    'score': float(score),
                    'metadata': results['metadatas'][0][idx] if results['metadatas'] else {}
                })
            
            return documents
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []