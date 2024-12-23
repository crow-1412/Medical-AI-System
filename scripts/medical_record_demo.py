"""病历管理功能演示脚本"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.new_agents.medical_record_agent import MedicalRecordAgent, RecordType, RecordStatus
from config.config import Config

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def demo_create_record(agent):
    """演示创建病历"""
    print_section("创建病历")
    record_data = {
        "patient_id": "P20230001",
        "record_type": RecordType.OUTPATIENT.value,
        "visit_date": datetime.now().strftime("%Y-%m-%d"),
        "department": "内科",
        "doctor": "张医生",
        "chief_complaint": "发热三天，咳嗽伴有白痰",
        "present_illness": "患者三天前无明显诱因出现发热，最高体温38.5℃，伴有咳嗽、白痰",
        "past_history": "否认高血压、糖尿病等慢性病史",
        "allergic_history": "青霉素过敏",
        "physical_examination": "体温38.2℃，心肺听诊无异常",
        "diagnosis": "上呼吸道感染",
        "treatment_plan": "对症治疗，注意休息"
    }
    record_id = agent.create_record(record_data, "张医生")
    print(f"创建病历成功: {record_id}")
    return record_id

def demo_add_examination(agent, record_id):
    """演示添加检查结果"""
    print_section("添加检查结果")
    exam_data = {
        "record_id": record_id,
        "exam_type": "血常规",
        "exam_date": datetime.now().strftime("%Y-%m-%d"),
        "exam_department": "检验科",
        "exam_doctor": "李医生",
        "exam_result": "白细胞计数：10.5×10^9/L，中性粒细胞比例：75%",
        "exam_conclusion": "白细胞计数轻度升高，考虑感染可能",
        "notes": "建议复查"
    }
    agent.add_examination(exam_data, "李医生")
    print("添加检查结果成功")

def demo_add_prescription(agent, record_id):
    """演示添加处方"""
    print_section("添加处方")
    prescription_data = {
        "record_id": record_id,
        "prescription_type": "西药处方",
        "medication_name": "布洛芬缓释胶囊",
        "specification": "0.3g",
        "dosage": "0.3g",
        "frequency": "每8小时一次",
        "duration": "3天",
        "usage": "口服",
        "quantity": 9,
        "unit": "粒",
        "notes": "饭后服用"
    }
    agent.add_prescription(prescription_data, "张医生")
    print("添加处方成功")

def demo_update_record(agent, record_id):
    """演示更新病历"""
    print_section("更新病历")
    update_data = {
        "diagnosis": "上呼吸道感染，病毒性感冒",
        "treatment_plan": "对症治疗，注意休息，多饮水",
        "record_status": RecordStatus.SUBMITTED.value
    }
    agent.update_record(record_id, update_data, "张医生")
    print("更新病历成功")

def demo_add_operation(agent, record_id):
    """演示添加手术记录"""
    print_section("添加手术记录")
    operation_data = {
        "record_id": record_id,
        "operation_name": "阑尾切除术",
        "operation_date": datetime.now().strftime("%Y-%m-%d"),
        "preoperative_diagnosis": "急性阑尾炎",
        "postoperative_diagnosis": "急性化脓性阑尾炎",
        "operation_level": "四级手术",
        "surgeon": "王医生",
        "assistant": "李医生",
        "anesthesiologist": "赵医生",
        "anesthesia_method": "全身麻醉",
        "operation_description": "手术顺利，切除阑尾",
        "blood_loss": 50,
        "notes": "术后恢复良好"
    }
    agent.add_operation_record(operation_data, "王医生")
    print("添加手术记录成功")

def demo_add_attachment(agent, record_id):
    """演示添加附件"""
    print_section("添加附件")
    attachment_data = {
        "record_id": record_id,
        "file_name": "CT检查报告.pdf",
        "file_type": "application/pdf",
        "file_path": "/path/to/ct_report.pdf",
        "file_size": 1024 * 1024  # 1MB
    }
    agent.add_attachment(attachment_data, "张医生")
    print("添加附件成功")

def demo_get_record(agent, record_id):
    """演示获取病历详情"""
    print_section("获取病历详情")
    record_info = agent.get_record(record_id, include_versions=True)
    print(json.dumps(record_info, ensure_ascii=False, indent=2))

def demo_search_records(agent):
    """演示搜索病历"""
    print_section("搜索病历")
    search_params = {
        "department": "内科",
        "date_range": [
            (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d")
        ],
        "diagnosis": "感染",
        "page": 1,
        "page_size": 10,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
    search_results = agent.search_records(search_params)
    print(f"找到 {len(search_results)} 条病历记录")
    for result in search_results:
        print(f"病历ID: {result['record_id']}, 患者ID: {result['patient_id']}, "
              f"诊断: {result['diagnosis']}")

def demo_export_records(agent, record_id):
    """演示导出病历"""
    print_section("导出病历")
    # JSON格式导出
    json_path = agent.export_records([record_id], "json")
    print(f"JSON导出路径: {json_path}")
    
    # Excel格式导出
    excel_path = agent.export_records([record_id], "excel")
    print(f"Excel导出路径: {excel_path}")
    
    # 包含附件的ZIP导出
    zip_path = agent.export_records([record_id], "excel", include_attachments=True)
    print(f"ZIP导出路径: {zip_path}")

def main():
    """主函数"""
    try:
        # 创建病历管理代理
        agent = MedicalRecordAgent(Config)
        
        # 演示各项功能
        record_id = demo_create_record(agent)
        demo_add_examination(agent, record_id)
        demo_add_prescription(agent, record_id)
        demo_update_record(agent, record_id)
        demo_add_operation(agent, record_id)
        demo_add_attachment(agent, record_id)
        demo_get_record(agent, record_id)
        demo_search_records(agent)
        demo_export_records(agent, record_id)
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
