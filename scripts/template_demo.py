import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from templates.report_templates import TemplateManager
from config.config import Config

def main():
    """主函数"""
    try:
        # 创建模板管理器
        manager = TemplateManager()
        
        # 展示所有默认模板
        print("默认模板列表：")
        for template in manager.list_templates():
            print(f"\n模板ID: {template['template_id']}")
            print(f"名称: {template['name']}")
            print(f"描述: {template['description']}")
            print(f"必需字段: {', '.join(template['required_fields'])}")
            print(f"可选字段: {', '.join(template['optional_fields'])}")
            
        # 创建自定义模板
        print("\n创建自定义模板...")
        custom_template = manager.create_custom_template(
            template_id="prescription",
            name="处方单",
            description="用于开具药品处方的标准模板",
            required_fields=[
                "patient_info",
                "diagnosis",
                "medications",
                "doctor_name",
                "prescription_date"
            ],
            optional_fields=[
                "notes",
                "allergies",
                "follow_up_date"
            ],
            template_format="""
处方单

患者信息：{patient_info}
诊断：{diagnosis}

开具药品：
{medications}

开具医师：{doctor_name}
开具日期：{prescription_date}

{notes}

过敏史：{allergies}
复诊日期：{follow_up_date}
"""
        )
        
        print("\n自定义模板创建成功！")
        
        # 使用模板生成报告示例
        print("\n生成报告示例：")
        
        # 1. 检查报告示例
        examination_data = {
            "patient_info": "张三，男，35岁",
            "examination_date": "2023-12-23",
            "examination_type": "心电图检查",
            "findings": "窦性心律，心率75次/分，各导联ST-T正常。",
            "conclusion": "心电图未见明显异常。",
            "doctor_name": "李医生",
            "department": "心内科",
            "equipment_info": "GE MAC 2000",
            "recommendations": "建议定期复查。",
            "notes": "检查过程顺利，患者配合良好。"
        }
        
        print("\n1. 检查报告示例：")
        print(manager.generate_report("examination_report", examination_data))
        
        # 2. 自定义处方单示例
        prescription_data = {
            "patient_info": "李四，女，28岁",
            "diagnosis": "上呼吸道感染",
            "medications": """
1. 布洛芬缓释胶囊 0.3g 口服 每12小时一次
2. 氯雷他定片 10mg 口服 每日一次
3. 板蓝根颗粒 10g 口服 每日三次""",
            "doctor_name": "王医生",
            "prescription_date": "2023-12-23",
            "notes": "饭后服用",
            "allergies": "对青霉素过敏",
            "follow_up_date": "2023-12-26"
        }
        
        print("\n2. 处方单示例：")
        print(manager.generate_report("prescription", prescription_data))
        
        # 保存模板配置
        templates_path = Path(Config.STORAGE_PATHS["output"]) / "templates.json"
        manager.save_templates(templates_path)
        print(f"\n模板配置已保存到: {templates_path}")
        
        # 测试加载模板
        print("\n测试加载模板...")
        new_manager = TemplateManager()
        new_manager.load_templates(templates_path)
        print("模板加载成功！")
        
        # 验证加载的模板
        loaded_templates = new_manager.list_templates()
        print(f"\n成功加载 {len(loaded_templates)} 个模板")
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
