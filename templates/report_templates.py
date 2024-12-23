import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
import logging

class BaseTemplate(ABC):
    """报告模板基类"""
    
    def __init__(self, template_id: str, name: str, description: str):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.required_fields = []
        self.optional_fields = []
        
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据是否符合模板要求"""
        pass
        
    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> str:
        """生成报告内容"""
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """将模板转换为字典格式"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields
        }

class ExaminationReportTemplate(BaseTemplate):
    """检查报告模板"""
    
    def __init__(self):
        super().__init__(
            template_id="examination_report",
            name="检查报告",
            description="用于记录各类医学检查结果的标准模板"
        )
        self.required_fields = [
            "patient_info",
            "examination_date",
            "examination_type",
            "findings",
            "conclusion"
        ]
        self.optional_fields = [
            "doctor_name",
            "department",
            "equipment_info",
            "notes",
            "recommendations"
        ]
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        # 检查必填字段
        for field in self.required_fields:
            if field not in data or not data[field]:
                return False
        return True
        
    def generate(self, data: Dict[str, Any]) -> str:
        """生成检查报告"""
        if not self.validate_data(data):
            raise ValueError("数据不完整，无法生成报告")
            
        report = f"""
检查报告

患者信息：{data['patient_info']}
检查日期：{data['examination_date']}
检查类型：{data['examination_type']}

检查发现：
{data['findings']}

结论：
{data['conclusion']}
"""
        
        # 添加可选字段
        if data.get('doctor_name'):
            report += f"\n检查医师：{data['doctor_name']}"
        if data.get('department'):
            report += f"\n检���科室：{data['department']}"
        if data.get('equipment_info'):
            report += f"\n设备信息：{data['equipment_info']}"
        if data.get('recommendations'):
            report += f"\n建议：\n{data['recommendations']}"
        if data.get('notes'):
            report += f"\n备注：\n{data['notes']}"
            
        # 添加报告时间
        report += f"\n\n报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report

class FollowUpRecordTemplate(BaseTemplate):
    """随访记录模板"""
    
    def __init__(self):
        super().__init__(
            template_id="follow_up_record",
            name="随访记录",
            description="用于记录患者随访情况的标准模板"
        )
        self.required_fields = [
            "patient_info",
            "follow_up_date",
            "follow_up_type",
            "current_status",
            "treatment_effect"
        ]
        self.optional_fields = [
            "chief_complaint",
            "vital_signs",
            "medication_status",
            "adverse_reactions",
            "next_follow_up",
            "doctor_name",
            "notes"
        ]
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        for field in self.required_fields:
            if field not in data or not data[field]:
                return False
        return True
        
    def generate(self, data: Dict[str, Any]) -> str:
        """生成随访记录"""
        if not self.validate_data(data):
            raise ValueError("数据不完整，无法生成记录")
            
        record = f"""
随访记录

患者信息：{data['patient_info']}
随访日期：{data['follow_up_date']}
随访方式：{data['follow_up_type']}

当前状态：
{data['current_status']}

治疗效果：
{data['treatment_effect']}
"""
        
        # 添加可选字段
        if data.get('chief_complaint'):
            record += f"\n主诉：\n{data['chief_complaint']}"
        if data.get('vital_signs'):
            record += f"\n生命体征：\n{data['vital_signs']}"
        if data.get('medication_status'):
            record += f"\n用药情况：\n{data['medication_status']}"
        if data.get('adverse_reactions'):
            record += f"\n不良反应：\n{data['adverse_reactions']}"
        if data.get('next_follow_up'):
            record += f"\n下次随访安排：{data['next_follow_up']}"
        if data.get('doctor_name'):
            record += f"\n随访医师：{data['doctor_name']}"
        if data.get('notes'):
            record += f"\n备注：\n{data['notes']}"
            
        record += f"\n\n记录生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return record

class ConsultationRecordTemplate(BaseTemplate):
    """会诊记录模板"""
    
    def __init__(self):
        super().__init__(
            template_id="consultation_record",
            name="会诊记录",
            description="用于记录多科室会诊情况的标准模板"
        )
        self.required_fields = [
            "patient_info",
            "consultation_date",
            "consultation_departments",
            "chief_complaint",
            "present_illness",
            "diagnosis",
            "treatment_plan"
        ]
        self.optional_fields = [
            "past_history",
            "examination_results",
            "consultation_findings",
            "recommendations",
            "doctors",
            "notes"
        ]
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        for field in self.required_fields:
            if field not in data or not data[field]:
                return False
        return True
        
    def generate(self, data: Dict[str, Any]) -> str:
        """生成会诊记录"""
        if not self.validate_data(data):
            raise ValueError("数据不完整，无法生成记录")
            
        record = f"""
会诊记录

患者信息：{data['patient_info']}
会诊日期：{data['consultation_date']}
会诊科室：{data['consultation_departments']}

主诉：
{data['chief_complaint']}

现病史：
{data['present_illness']}

诊断：
{data['diagnosis']}

治疗方案：
{data['treatment_plan']}
"""
        
        # 添加可选字段
        if data.get('past_history'):
            record += f"\n既往史：\n{data['past_history']}"
        if data.get('examination_results'):
            record += f"\n检查结果：\n{data['examination_results']}"
        if data.get('consultation_findings'):
            record += f"\n会诊意见：\n{data['consultation_findings']}"
        if data.get('recommendations'):
            record += f"\n建议：\n{data['recommendations']}"
        if data.get('doctors'):
            record += f"\n参与医师：{data['doctors']}"
        if data.get('notes'):
            record += f"\n备注：\n{data['notes']}"
            
        record += f"\n\n记录生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return record

class DischargeSummaryTemplate(BaseTemplate):
    """出院小结模板"""
    
    def __init__(self):
        super().__init__(
            template_id="discharge_summary",
            name="出院小结",
            description="用于记录患者出院情况的标准模板"
        )
        self.required_fields = [
            "patient_info",
            "admission_date",
            "discharge_date",
            "admission_diagnosis",
            "discharge_diagnosis",
            "treatment_course",
            "discharge_status",
            "discharge_orders"
        ]
        self.optional_fields = [
            "chief_complaint",
            "present_illness",
            "past_history",
            "examination_results",
            "operation_records",
            "medication_record",
            "follow_up_plan",
            "doctor_name",
            "notes"
        ]
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        for field in self.required_fields:
            if field not in data or not data[field]:
                return False
        return True
        
    def generate(self, data: Dict[str, Any]) -> str:
        """生成出院小结"""
        if not self.validate_data(data):
            raise ValueError("数据不完整，无法生成小结")
            
        summary = f"""
出院小结

患者信息：{data['patient_info']}
入院日期：{data['admission_date']}
出院日期：{data['discharge_date']}

入院诊断：
{data['admission_diagnosis']}

出院诊断：
{data['discharge_diagnosis']}

治疗经过：
{data['treatment_course']}

出院情况：
{data['discharge_status']}

出院医嘱：
{data['discharge_orders']}
"""
        
        # 添加可选字段
        if data.get('chief_complaint'):
            summary += f"\n主诉：\n{data['chief_complaint']}"
        if data.get('present_illness'):
            summary += f"\n现病史：\n{data['present_illness']}"
        if data.get('past_history'):
            summary += f"\n既往史：\n{data['past_history']}"
        if data.get('examination_results'):
            summary += f"\n检查结果：\n{data['examination_results']}"
        if data.get('operation_records'):
            summary += f"\n手术记录：\n{data['operation_records']}"
        if data.get('medication_record'):
            summary += f"\n用药记录：\n{data['medication_record']}"
        if data.get('follow_up_plan'):
            summary += f"\n随访计划：\n{data['follow_up_plan']}"
        if data.get('doctor_name'):
            summary += f"\n主治医师：{data['doctor_name']}"
        if data.get('notes'):
            summary += f"\n备注：\n{data['notes']}"
            
        summary += f"\n\n小结生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return summary

class CustomTemplate(BaseTemplate):
    """自定义模板"""
    
    def __init__(self, template_id: str, name: str, description: str, 
                 required_fields: List[str], optional_fields: List[str],
                 template_format: str):
        super().__init__(template_id, name, description)
        self.required_fields = required_fields
        self.optional_fields = optional_fields
        self.template_format = template_format
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        for field in self.required_fields:
            if field not in data or not data[field]:
                return False
        return True
        
    def generate(self, data: Dict[str, Any]) -> str:
        """生成报告内容"""
        if not self.validate_data(data):
            raise ValueError("数据不完整，无法生成报告")
            
        try:
            # 使用数据填充模板
            report = self.template_format.format(**data)
            # 添加生成时间
            report += f"\n\n报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return report
        except KeyError as e:
            raise ValueError(f"模板中包含未提供的字段: {str(e)}")
        except Exception as e:
            raise ValueError(f"生成报告时出错: {str(e)}")
            
    def to_dict(self) -> Dict[str, Any]:
        """将模板转换为字典格式"""
        template_dict = super().to_dict()
        template_dict.update({
            "template_format": self.template_format,
            "type": "custom"
        })
        return template_dict
        
class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        self.templates: Dict[str, BaseTemplate] = {}
        self._load_default_templates()
        
    def _load_default_templates(self):
        """加载默认模板"""
        default_templates = [
            ExaminationReportTemplate(),
            FollowUpRecordTemplate(),
            ConsultationRecordTemplate(),
            DischargeSummaryTemplate()
        ]
        
        for template in default_templates:
            self.register_template(template)
            
    def register_template(self, template: BaseTemplate):
        """注册新模板"""
        if not isinstance(template, BaseTemplate):
            raise TypeError("模板必须继承自 BaseTemplate")
            
        self.templates[template.template_id] = template
        
    def get_template(self, template_id: str) -> Optional[BaseTemplate]:
        """获取指定模板"""
        return self.templates.get(template_id)
        
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用模板"""
        return [template.to_dict() for template in self.templates.values()]
        
    def generate_report(self, template_id: str, data: Dict[str, Any]) -> str:
        """使用指定模板生成报告"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"未找到模板: {template_id}")
            
        return template.generate(data)
        
    def create_custom_template(self, template_id: str, name: str, description: str,
                             required_fields: List[str], optional_fields: List[str],
                             template_format: str) -> CustomTemplate:
        """创建自定义模板"""
        if template_id in self.templates:
            raise ValueError(f"模板ID已存在: {template_id}")
            
        template = CustomTemplate(
            template_id=template_id,
            name=name,
            description=description,
            required_fields=required_fields,
            optional_fields=optional_fields,
            template_format=template_format
        )
        
        self.register_template(template)
        return template
        
    def save_templates(self, save_path: Path):
        """保存模板配置"""
        templates_data = {
            template_id: template.to_dict()
            for template_id, template in self.templates.items()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, ensure_ascii=False, indent=2)
            
    def load_templates(self, load_path: Path):
        """加载模板配置"""
        if not load_path.exists():
            return
            
        with open(load_path, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
            
        # 清除现有模板
        self.templates.clear()
        
        # 重新加载默认模板
        self._load_default_templates()
        
        # 加载自定义模板
        for template_id, template_data in templates_data.items():
            if template_data.get("type") == "custom":
                try:
                    self.create_custom_template(
                        template_id=template_id,
                        name=template_data["name"],
                        description=template_data["description"],
                        required_fields=template_data["required_fields"],
                        optional_fields=template_data["optional_fields"],
                        template_format=template_data["template_format"]
                    )
                except Exception as e:
                    logging.error(f"加载模板 {template_id} 失败: {str(e)}")
                    continue
                    
    def remove_template(self, template_id: str):
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            
    def update_template(self, template_id: str, **kwargs):
        """更新模板"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"未找到模板: {template_id}")
            
        if isinstance(template, CustomTemplate):
            # 更新自定义模板
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
        else:
            raise ValueError("只能更新自定义模板")