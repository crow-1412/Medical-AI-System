"""医疗记录分析器"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import Counter
import sqlite3
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    """分析结果"""
    title: str
    description: str
    data: Any
    chart_path: str = None

class MedicalRecordAnalyzer:
    """医疗记录分析器"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.chart_dir = db_path.parent / "charts"
        self.chart_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(str(self.db_path))
        
    def analyze_visit_trends(self, start_date: str, end_date: str) -> AnalysisResult:
        """分析就诊趋势"""
        conn = self._get_connection()
        
        # 查询就诊数据
        df = pd.read_sql_query("""
            SELECT visit_date, record_type, department
            FROM medical_records
            WHERE visit_date BETWEEN ? AND ?
        """, conn, params=[start_date, end_date])
        
        # 转换日期格式
        df["visit_date"] = pd.to_datetime(df["visit_date"])
        
        # 按日期统计就诊人数
        daily_visits = df.groupby("visit_date").size().reset_index(name="visits")
        
        # 按科室统计就诊人数
        dept_visits = df.groupby("department").size().sort_values(ascending=False)
        
        # 按就诊类型统计
        type_visits = df.groupby("record_type").size()
        
        # 生成趋势图
        plt.figure(figsize=(12, 6))
        plt.plot(daily_visits["visit_date"], daily_visits["visits"], marker="o")
        plt.title("每日就诊人数趋势")
        plt.xlabel("日期")
        plt.ylabel("就诊人数")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.chart_dir / f"visit_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path)
        plt.close()
        
        # 生成分析结果
        description = f"""
        分析周期: {start_date} 至 {end_date}
        总就诊人数: {len(df)}
        日均就诊人数: {len(df) / len(daily_visits):.1f}
        最高日就诊量: {daily_visits['visits'].max()} ({daily_visits.loc[daily_visits['visits'].idxmax(), 'visit_date'].strftime('%Y-%m-%d')})
        就诊类型分布: {dict(type_visits)}
        就诊量前三科室: {dict(dept_visits.head(3))}
        """
        
        return AnalysisResult(
            title="就诊趋势分析",
            description=description,
            data={
                "daily_visits": daily_visits.to_dict("records"),
                "department_visits": dept_visits.to_dict(),
                "type_visits": type_visits.to_dict()
            },
            chart_path=str(chart_path)
        )
        
    def analyze_diagnosis_distribution(self) -> AnalysisResult:
        """分析诊断分布"""
        conn = self._get_connection()
        
        # 查询诊断数据
        df = pd.read_sql_query("""
            SELECT diagnosis, department
            FROM medical_records
            WHERE diagnosis IS NOT NULL
        """, conn)
        
        # 统计诊断频次
        diagnosis_counts = df["diagnosis"].value_counts()
        
        # 按科室统计诊断分布
        dept_diagnosis = df.groupby("department")["diagnosis"].agg(list)
        dept_top_diagnosis = {
            dept: Counter(diagnoses).most_common(3)
            for dept, diagnoses in dept_diagnosis.items()
        }
        
        # 生成诊断分布图
        plt.figure(figsize=(12, 6))
        diagnosis_counts.head(10).plot(kind="bar")
        plt.title("前10位常见诊断")
        plt.xlabel("诊断")
        plt.ylabel("频次")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.chart_dir / f"diagnosis_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path)
        plt.close()
        
        # 生成分析结果
        description = f"""
        总诊断数: {len(df)}
        不同诊断数: {len(diagnosis_counts)}
        最常见诊断:
        {pd.DataFrame(diagnosis_counts.head().items(), columns=['诊断', '频次']).to_string(index=False)}
        
        各科室常见诊断:
        {json.dumps(dept_top_diagnosis, ensure_ascii=False, indent=2)}
        """
        
        return AnalysisResult(
            title="诊断分布分析",
            description=description,
            data={
                "diagnosis_counts": diagnosis_counts.to_dict(),
                "department_diagnosis": dept_top_diagnosis
            },
            chart_path=str(chart_path)
        )
        
    def analyze_examination_statistics(self) -> AnalysisResult:
        """分析检查统计"""
        conn = self._get_connection()
        
        # 查询检查数据
        df = pd.read_sql_query("""
            SELECT e.*, r.department
            FROM examination_results e
            JOIN medical_records r ON e.record_id = r.record_id
        """, conn)
        
        # 统计检查类型分布
        exam_type_counts = df["exam_type"].value_counts()
        
        # 按科室统计检查分布
        dept_exam_counts = df.groupby(["department", "exam_type"]).size().unstack(fill_value=0)
        
        # 生成检查类型分布图
        plt.figure(figsize=(10, 6))
        exam_type_counts.plot(kind="pie", autopct="%1.1f%%")
        plt.title("检查类型分布")
        plt.axis("equal")
        
        # 保存图表
        chart_path = self.chart_dir / f"examination_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path)
        plt.close()
        
        # 生成分析结果
        description = f"""
        总检查数: {len(df)}
        检查类型数: {len(exam_type_counts)}
        检查类型分布:
        {pd.DataFrame(exam_type_counts.items(), columns=['检查类型', '次数']).to_string(index=False)}
        
        各科室检查情况:
        {dept_exam_counts.to_string()}
        """
        
        return AnalysisResult(
            title="检查统计分析",
            description=description,
            data={
                "exam_type_counts": exam_type_counts.to_dict(),
                "department_exam_counts": dept_exam_counts.to_dict()
            },
            chart_path=str(chart_path)
        )
        
    def analyze_prescription_patterns(self) -> AnalysisResult:
        """分析处方模式"""
        conn = self._get_connection()
        
        # 查询处方数据
        df = pd.read_sql_query("""
            SELECT p.*, r.department, r.diagnosis
            FROM prescriptions p
            JOIN medical_records r ON p.record_id = r.record_id
        """, conn)
        
        # 统计药品使用频次
        med_counts = df["medication_name"].value_counts()
        
        # 按科室统计用药情况
        dept_med_counts = df.groupby(["department", "medication_name"]).size().unstack(fill_value=0)
        
        # 分析诊断-用药关系
        diag_med = df.groupby("diagnosis")["medication_name"].agg(list)
        diag_med_patterns = {
            diag: Counter(meds).most_common(3)
            for diag, meds in diag_med.items()
        }
        
        # 生成药品使用频次图
        plt.figure(figsize=(12, 6))
        med_counts.head(10).plot(kind="bar")
        plt.title("前10位常用药品")
        plt.xlabel("药品名称")
        plt.ylabel("使用频次")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.chart_dir / f"prescription_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path)
        plt.close()
        
        # 生成分析结果
        description = f"""
        总处方数: {len(df)}
        不同药品数: {len(med_counts)}
        最常用药品:
        {pd.DataFrame(med_counts.head().items(), columns=['药品', '频次']).to_string(index=False)}
        
        各科室用药特点:
        {dept_med_counts.to_string()}
        
        典型诊断用药模式:
        {json.dumps(dict(list(diag_med_patterns.items())[:5]), ensure_ascii=False, indent=2)}
        """
        
        return AnalysisResult(
            title="处方模式分析",
            description=description,
            data={
                "medication_counts": med_counts.to_dict(),
                "department_medication_counts": dept_med_counts.to_dict(),
                "diagnosis_medication_patterns": diag_med_patterns
            },
            chart_path=str(chart_path)
        )
        
    def analyze_operation_statistics(self) -> AnalysisResult:
        """分析手术统计"""
        conn = self._get_connection()
        
        # 查询手术数据
        df = pd.read_sql_query("""
            SELECT o.*, r.department
            FROM operation_records o
            JOIN medical_records r ON o.record_id = r.record_id
        """, conn)
        
        # 统计手术类型分布
        op_counts = df["operation_name"].value_counts()
        
        # 按科室统计手术情况
        dept_op_counts = df.groupby(["department", "operation_name"]).size().unstack(fill_value=0)
        
        # 统计手术等级分布
        level_counts = df["operation_level"].value_counts()
        
        # 生成手术等级分布图
        plt.figure(figsize=(8, 8))
        plt.pie(level_counts.values, labels=level_counts.index, autopct="%1.1f%%")
        plt.title("手术等级分布")
        plt.axis("equal")
        
        # 保存图表
        chart_path = self.chart_dir / f"operation_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path)
        plt.close()
        
        # 计算平均手术时长和出血量
        avg_stats = {
            "avg_blood_loss": df["blood_loss"].mean(),
            "max_blood_loss": df["blood_loss"].max(),
            "min_blood_loss": df["blood_loss"].min()
        }
        
        # 生成分析结果
        description = f"""
        总手术数: {len(df)}
        不同手术类型数: {len(op_counts)}
        最常见手术:
        {pd.DataFrame(op_counts.head().items(), columns=['手术名称', '次数']).to_string(index=False)}
        
        手术等级分布:
        {pd.DataFrame(level_counts.items(), columns=['等级', '次数']).to_string(index=False)}
        
        手术统计:
        - 平均出血量: {avg_stats['avg_blood_loss']:.1f}ml
        - 最大出血量: {avg_stats['max_blood_loss']}ml
        - 最小出血量: {avg_stats['min_blood_loss']}ml
        
        各科室手术情况:
        {dept_op_counts.to_string()}
        """
        
        return AnalysisResult(
            title="手术统计分析",
            description=description,
            data={
                "operation_counts": op_counts.to_dict(),
                "level_counts": level_counts.to_dict(),
                "department_operation_counts": dept_op_counts.to_dict(),
                "average_stats": avg_stats
            },
            chart_path=str(chart_path)
        )
        
    def generate_summary_report(self, start_date: str, end_date: str) -> str:
        """生成汇总报告"""
        # 获取各项分析结果
        visit_analysis = self.analyze_visit_trends(start_date, end_date)
        diagnosis_analysis = self.analyze_diagnosis_distribution()
        examination_analysis = self.analyze_examination_statistics()
        prescription_analysis = self.analyze_prescription_patterns()
        operation_analysis = self.analyze_operation_statistics()
        
        # 生成报告文件
        report_dir = self.db_path.parent / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 医疗记录分析报告\n\n")
            f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析周期: {start_date} 至 {end_date}\n\n")
            
            # 写入各项分析结果
            for analysis in [visit_analysis, diagnosis_analysis, examination_analysis,
                           prescription_analysis, operation_analysis]:
                f.write(f"## {analysis.title}\n\n")
                f.write(analysis.description)
                f.write("\n\n")
                if analysis.chart_path:
                    f.write(f"![{analysis.title}]({analysis.chart_path})\n\n")
                    
        return str(report_path)
