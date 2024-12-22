from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup

class DataProcessor:
    @staticmethod
    def clean_html(html_content: str) -> str:
        """清理HTML内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text()
        
    @staticmethod
    def extract_medical_terms(text: str) -> List[str]:
        """提取医学术语"""
        # 这里需要根据具体需求实现医学术语提取逻辑
        return []
        
    @staticmethod
    def chunk_document(text: str, chunk_size: int, overlap: int) -> List[str]:
        """文档分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            chunks.append(text[start:end])
            start = end - overlap
        return chunks
        
    @staticmethod
    def format_medical_report(report_data: Dict[str, Any]) -> str:
        """格式化医疗报告"""
        template = """
        患者信息：{patient_info}
        诊断结果：{diagnosis}
        治疗建议：{treatment}
        注意事项：{notes}
        """
        return template.format(**report_data) 