"""医疗记录验证器"""

from typing import List, Dict, Any
from datetime import datetime
import re
from dataclasses import dataclass
from enum import Enum

@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    code: str

class ValidationType(Enum):
    """验证类型"""
    REQUIRED = "required"  # 必填
    FORMAT = "format"      # 格式
    RANGE = "range"       # 范围
    ENUM = "enum"         # 枚举
    REGEX = "regex"       # 正则表达式
    CUSTOM = "custom"     # 自定义

class MedicalRecordValidator:
    """医疗记录验证器"""
    
    def __init__(self):
        # 定义字段验证规则
        self.field_rules = {
            # 基本信息验证规则
            "patient_id": [
                {"type": ValidationType.REQUIRED, "message": "患者ID不能为空"},
                {"type": ValidationType.REGEX, "pattern": r"^P\d{8}$", "message": "患者ID格式不正确(P+8位数字)"}
            ],
            "record_type": [
                {"type": ValidationType.REQUIRED, "message": "病历类型不能为空"},
                {"type": ValidationType.ENUM, "values": ["门诊", "住院", "急诊", "体检"], "message": "无效的病历类型"}
            ],
            "visit_date": [
                {"type": ValidationType.REQUIRED, "message": "就诊日期不能为空"},
                {"type": ValidationType.FORMAT, "format": "%Y-%m-%d", "message": "日期格式不正确(YYYY-MM-DD)"},
                {"type": ValidationType.CUSTOM, "validator": self._validate_visit_date, "message": "就诊日期不能晚于今天"}
            ],
            "department": [
                {"type": ValidationType.REQUIRED, "message": "科室不能为空"}
            ],
            "doctor": [
                {"type": ValidationType.REQUIRED, "message": "医生不能为空"}
            ],
            
            # 病历内容验证规则
            "chief_complaint": [
                {"type": ValidationType.REQUIRED, "message": "主诉不能为空"},
                {"type": ValidationType.RANGE, "min_length": 2, "max_length": 500, "message": "主诉长度必须在2-500字之间"}
            ],
            "present_illness": [
                {"type": ValidationType.REQUIRED, "message": "现病史不能为空"},
                {"type": ValidationType.RANGE, "min_length": 10, "max_length": 2000, "message": "现病史长度必须在10-2000字之间"}
            ],
            "diagnosis": [
                {"type": ValidationType.REQUIRED, "message": "诊断不能为空"}
            ],
            
            # 检查结果验证规则
            "exam_type": [
                {"type": ValidationType.REQUIRED, "message": "检查类型不能为空"}
            ],
            "exam_date": [
                {"type": ValidationType.REQUIRED, "message": "检查日期不能为空"},
                {"type": ValidationType.FORMAT, "format": "%Y-%m-%d", "message": "日期格式不正确(YYYY-MM-DD)"}
            ],
            "exam_result": [
                {"type": ValidationType.REQUIRED, "message": "检查结果不能为空"}
            ],
            
            # 处方验证规则
            "medication_name": [
                {"type": ValidationType.REQUIRED, "message": "药品名称不能为空"}
            ],
            "dosage": [
                {"type": ValidationType.REQUIRED, "message": "用药剂量不能为空"},
                {"type": ValidationType.REGEX, "pattern": r"^\d+\.?\d*[a-zA-Z]+$", "message": "剂量格式不正确(如: 0.3g)"}
            ],
            "frequency": [
                {"type": ValidationType.REQUIRED, "message": "用药频次不能为空"}
            ],
            "duration": [
                {"type": ValidationType.REQUIRED, "message": "用药天数不能为空"}
            ],
            
            # 手术记录验证规则
            "operation_name": [
                {"type": ValidationType.REQUIRED, "message": "手术名称不能为空"}
            ],
            "operation_date": [
                {"type": ValidationType.REQUIRED, "message": "手术日期不能为空"},
                {"type": ValidationType.FORMAT, "format": "%Y-%m-%d", "message": "日期格式不正确(YYYY-MM-DD)"}
            ],
            "surgeon": [
                {"type": ValidationType.REQUIRED, "message": "主刀医生不能为空"}
            ],
            "operation_level": [
                {"type": ValidationType.REQUIRED, "message": "手术等级不能为空"},
                {"type": ValidationType.ENUM, "values": ["一级", "二级", "三级", "四级"], "message": "无效的手术等级"}
            ],
            
            # 附件验证规则
            "file_name": [
                {"type": ValidationType.REQUIRED, "message": "文件名不能为空"},
                {"type": ValidationType.REGEX, "pattern": r"^[\w\-. ]+$", "message": "文件名包含非法字符"}
            ],
            "file_type": [
                {"type": ValidationType.REQUIRED, "message": "文件类型不能为空"},
                {"type": ValidationType.ENUM, 
                 "values": ["application/pdf", "image/jpeg", "image/png", "application/msword",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                 "message": "不支持的文件类型"}
            ],
            "file_size": [
                {"type": ValidationType.RANGE, "min": 0, "max": 100*1024*1024, "message": "文件大小超过限制(100MB)"}
            ]
        }
        
    def _validate_required(self, value: Any, rule: Dict) -> List[ValidationError]:
        """验证必填字段"""
        if not value and value != 0:
            return [ValidationError(field="", message=rule["message"], code="required")]
        return []
        
    def _validate_format(self, value: str, rule: Dict) -> List[ValidationError]:
        """验证日期格式"""
        try:
            if value:
                datetime.strptime(value, rule["format"])
            return []
        except ValueError:
            return [ValidationError(field="", message=rule["message"], code="format")]
            
    def _validate_range(self, value: Any, rule: Dict) -> List[ValidationError]:
        """验证范围"""
        errors = []
        if "min_length" in rule and len(str(value)) < rule["min_length"]:
            errors.append(ValidationError(field="", message=rule["message"], code="range"))
        if "max_length" in rule and len(str(value)) > rule["max_length"]:
            errors.append(ValidationError(field="", message=rule["message"], code="range"))
        if "min" in rule and value < rule["min"]:
            errors.append(ValidationError(field="", message=rule["message"], code="range"))
        if "max" in rule and value > rule["max"]:
            errors.append(ValidationError(field="", message=rule["message"], code="range"))
        return errors
        
    def _validate_enum(self, value: str, rule: Dict) -> List[ValidationError]:
        """验证枚举值"""
        if value not in rule["values"]:
            return [ValidationError(field="", message=rule["message"], code="enum")]
        return []
        
    def _validate_regex(self, value: str, rule: Dict) -> List[ValidationError]:
        """验证正则表达式"""
        if not re.match(rule["pattern"], value):
            return [ValidationError(field="", message=rule["message"], code="regex")]
        return []
        
    def _validate_visit_date(self, value: str) -> List[ValidationError]:
        """验证就诊日期"""
        visit_date = datetime.strptime(value, "%Y-%m-%d")
        if visit_date.date() > datetime.now().date():
            return [ValidationError(field="", message="就诊日期不能晚于今天", code="custom")]
        return []
        
    def validate_field(self, field: str, value: Any) -> List[ValidationError]:
        """验证单个字段"""
        if field not in self.field_rules:
            return []
            
        errors = []
        for rule in self.field_rules[field]:
            rule_type = ValidationType(rule["type"])
            
            if rule_type == ValidationType.REQUIRED:
                errors.extend(self._validate_required(value, rule))
            elif rule_type == ValidationType.FORMAT:
                errors.extend(self._validate_format(value, rule))
            elif rule_type == ValidationType.RANGE:
                errors.extend(self._validate_range(value, rule))
            elif rule_type == ValidationType.ENUM:
                errors.extend(self._validate_enum(value, rule))
            elif rule_type == ValidationType.REGEX:
                errors.extend(self._validate_regex(value, rule))
            elif rule_type == ValidationType.CUSTOM:
                errors.extend(rule["validator"](value))
                
            # 如果是必填字段且为空，不再进行后续验证
            if rule_type == ValidationType.REQUIRED and errors:
                break
                
        for error in errors:
            error.field = field
            
        return errors
        
    def validate_record(self, record_data: Dict[str, Any]) -> List[ValidationError]:
        """验证病历记录"""
        errors = []
        
        # 验证每个字段
        for field, value in record_data.items():
            field_errors = self.validate_field(field, value)
            errors.extend(field_errors)
            
        return errors
        
    def validate_examination(self, exam_data: Dict[str, Any]) -> List[ValidationError]:
        """验证检查结果"""
        errors = []
        required_fields = ["exam_type", "exam_date", "exam_result"]
        
        for field in required_fields:
            if field in exam_data:
                field_errors = self.validate_field(field, exam_data[field])
                errors.extend(field_errors)
                
        return errors
        
    def validate_prescription(self, prescription_data: Dict[str, Any]) -> List[ValidationError]:
        """验证处方"""
        errors = []
        required_fields = ["medication_name", "dosage", "frequency", "duration"]
        
        for field in required_fields:
            if field in prescription_data:
                field_errors = self.validate_field(field, prescription_data[field])
                errors.extend(field_errors)
                
        return errors
        
    def validate_operation(self, operation_data: Dict[str, Any]) -> List[ValidationError]:
        """验证手术记录"""
        errors = []
        required_fields = ["operation_name", "operation_date", "surgeon", "operation_level"]
        
        for field in required_fields:
            if field in operation_data:
                field_errors = self.validate_field(field, operation_data[field])
                errors.extend(field_errors)
                
        return errors
        
    def validate_attachment(self, attachment_data: Dict[str, Any]) -> List[ValidationError]:
        """验证附件"""
        errors = []
        required_fields = ["file_name", "file_type"]
        
        for field in required_fields:
            if field in attachment_data:
                field_errors = self.validate_field(field, attachment_data[field])
                errors.extend(field_errors)
                
        # 验证文件大小
        if "file_size" in attachment_data:
            field_errors = self.validate_field("file_size", attachment_data["file_size"])
            errors.extend(field_errors)
            
        return errors
