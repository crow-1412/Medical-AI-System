from typing import Dict, Any

class ReportTemplates:
    @staticmethod
    def get_template(report_type: str) -> str:
        """获取报告模板"""
        templates = {
            "初步诊断报告": """
主诉：{chief_complaint}
现病史：{present_illness}
体格检查：{physical_exam}
初步诊断：{diagnosis}
治疗建议：{treatment}
""",
            "住院记录": """
入院时间：{admission_time}
科室：{department}
主诉：{chief_complaint}
现病史：{present_illness}
既往史：{past_history}
体格检查：{physical_exam}
辅助检查：{auxiliary_exam}
诊断：{diagnosis}
治疗计划：{treatment_plan}
""",
            "手术记录": """
手术日期：{operation_date}
手术名称：{operation_name}
手术医师：{surgeon}
麻醉方式：{anesthesia}
手术经过：{operation_process}
手术结果：{operation_result}
注意事项：{notes}
"""
        }
        return templates.get(report_type, "") 