"""医疗记录分析演示脚本"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.new_agents.medical_record_analyzer import MedicalRecordAnalyzer
from config.config import Config

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def main():
    """主函数"""
    try:
        # 确保目录存在
        Config.init_dirs()
        
        # 创建分析器
        analyzer = MedicalRecordAnalyzer(Config.DB_PATH)
        
        # 设置分析时间范围
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # 1. 分析就诊趋势
        print_section("1. 分析就诊趋势")
        visit_analysis = analyzer.analyze_visit_trends(start_date, end_date)
        print(visit_analysis.description)
        print(f"趋势图保存至: {visit_analysis.chart_path}")
        
        # 2. 分析诊断分布
        print_section("2. 分析诊断分布")
        diagnosis_analysis = analyzer.analyze_diagnosis_distribution()
        print(diagnosis_analysis.description)
        print(f"分布图保存至: {diagnosis_analysis.chart_path}")
        
        # 3. 分析检查统计
        print_section("3. 分析检查统计")
        examination_analysis = analyzer.analyze_examination_statistics()
        print(examination_analysis.description)
        print(f"统计图保存至: {examination_analysis.chart_path}")
        
        # 4. 分析处方模式
        print_section("4. 分析处方模式")
        prescription_analysis = analyzer.analyze_prescription_patterns()
        print(prescription_analysis.description)
        print(f"模式图保存至: {prescription_analysis.chart_path}")
        
        # 5. 分析手术统计
        print_section("5. 分析手术统计")
        operation_analysis = analyzer.analyze_operation_statistics()
        print(operation_analysis.description)
        print(f"统计图保存至: {operation_analysis.chart_path}")
        
        # 6. 生成汇总报告
        print_section("6. 生成汇总报告")
        report_path = analyzer.generate_summary_report(start_date, end_date)
        print(f"汇总报告保存至: {report_path}")
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
