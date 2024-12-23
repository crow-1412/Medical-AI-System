"""医疗记录管理代理"""

import sqlite3
from pathlib import Path
import json
from datetime import datetime
import uuid
import logging
from enum import Enum
import pandas as pd

class RecordType(Enum):
    """病历类型"""
    OUTPATIENT = "门诊"
    INPATIENT = "住院"
    EMERGENCY = "急诊"
    PHYSICAL = "体检"

class RecordStatus(Enum):
    """病历状态"""
    DRAFT = "草稿"
    SUBMITTED = "已提交"
    REVIEWED = "已审核"
    SIGNED = "已签名"
    ARCHIVED = "已归档"

class MedicalRecordAgent:
    """医疗记录管理代理"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.db_path = config.DB_PATH
        
        # 设置日志
        self.logger = logging.getLogger("MedicalRecordAgent")
        self.logger.setLevel(config.LOG_LEVEL)
        
        # 创建文件处理器
        log_file = config.LOGS_DIR / f"medical_record_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        self.logger.addHandler(file_handler)
        
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(str(self.db_path))
        
    def create_record(self, record_data: dict, created_by: str) -> str:
        """创建病历记录"""
        try:
            # 生成记录ID
            record_id = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 添加创建和更新信息
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record_data.update({
                "record_id": record_id,
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": created_by,
                "updated_by": created_by,
                "record_status": RecordStatus.DRAFT.value
            })
            
            # 构建SQL
            fields = ", ".join(record_data.keys())
            placeholders = ", ".join(["?" for _ in record_data])
            sql = f"INSERT INTO medical_records ({fields}) VALUES ({placeholders})"
            
            # 执行插入
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(record_data.values()))
            
            # 创建版本记录
            version_data = {
                "version_id": str(uuid.uuid4()),
                "record_id": record_id,
                "version": 1,
                "content": json.dumps(record_data, ensure_ascii=False),
                "changed_fields": json.dumps(list(record_data.keys()), ensure_ascii=False),
                "changed_at": current_time,
                "changed_by": created_by
            }
            
            fields = ", ".join(version_data.keys())
            placeholders = ", ".join(["?" for _ in version_data])
            sql = f"INSERT INTO record_versions ({fields}) VALUES ({placeholders})"
            cursor.execute(sql, list(version_data.values()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"创建病历记录成功: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"创建病历记录失败: {str(e)}")
            raise
            
    def get_record(self, record_id: str, include_versions: bool = False) -> dict:
        """获取病历记录"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取基本信息
            cursor.execute("SELECT * FROM medical_records WHERE record_id = ?", (record_id,))
            record = cursor.fetchone()
            
            if not record:
                raise ValueError(f"病历记录不存在: {record_id}")
                
            # 转换为字典
            columns = [desc[0] for desc in cursor.description]
            record_dict = dict(zip(columns, record))
            
            # 获取检查结果
            cursor.execute("SELECT * FROM examination_results WHERE record_id = ?", (record_id,))
            examinations = [dict(zip([desc[0] for desc in cursor.description], row))
                          for row in cursor.fetchall()]
            record_dict["examinations"] = examinations
            
            # 获取处方信息
            cursor.execute("SELECT * FROM prescriptions WHERE record_id = ?", (record_id,))
            prescriptions = [dict(zip([desc[0] for desc in cursor.description], row))
                           for row in cursor.fetchall()]
            record_dict["prescriptions"] = prescriptions
            
            # 获取手术记录
            cursor.execute("SELECT * FROM operation_records WHERE record_id = ?", (record_id,))
            operations = [dict(zip([desc[0] for desc in cursor.description], row))
                         for row in cursor.fetchall()]
            record_dict["operations"] = operations
            
            # 获取附件信息
            cursor.execute("SELECT * FROM record_attachments WHERE record_id = ?", (record_id,))
            attachments = [dict(zip([desc[0] for desc in cursor.description], row))
                          for row in cursor.fetchall()]
            record_dict["attachments"] = attachments
            
            # 获取版本历史
            if include_versions:
                cursor.execute("SELECT * FROM record_versions WHERE record_id = ? ORDER BY version",
                             (record_id,))
                versions = [dict(zip([desc[0] for desc in cursor.description], row))
                           for row in cursor.fetchall()]
                record_dict["versions"] = versions
                
            conn.close()
            return record_dict
            
        except Exception as e:
            self.logger.error(f"获取病历记录失败: {str(e)}")
            raise
            
    def update_record(self, record_id: str, update_data: dict, updated_by: str):
        """更新病历记录"""
        try:
            # 获取当前记录
            current_record = self.get_record(record_id)
            
            # 更新时间和操作人
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_data.update({
                "updated_at": current_time,
                "updated_by": updated_by
            })
            
            # 构建SQL
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            sql = f"UPDATE medical_records SET {set_clause} WHERE record_id = ?"
            
            # 执行更新
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(update_data.values()) + [record_id])
            
            # 创建版本记录
            version_data = {
                "version_id": str(uuid.uuid4()),
                "record_id": record_id,
                "version": len(current_record.get("versions", [])) + 1,
                "content": json.dumps({**current_record, **update_data}, ensure_ascii=False),
                "changed_fields": json.dumps(list(update_data.keys()), ensure_ascii=False),
                "changed_at": current_time,
                "changed_by": updated_by
            }
            
            fields = ", ".join(version_data.keys())
            placeholders = ", ".join(["?" for _ in version_data])
            sql = f"INSERT INTO record_versions ({fields}) VALUES ({placeholders})"
            cursor.execute(sql, list(version_data.values()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"更新病历记录成功: {record_id}")
            
        except Exception as e:
            self.logger.error(f"更新病历记录失败: {str(e)}")
            raise
            
    def add_examination(self, exam_data: dict, created_by: str):
        """添加检查结果"""
        try:
            # 生成检查ID
            exam_data["exam_id"] = f"E{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 添加创建信息
            exam_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            exam_data["created_by"] = created_by
            
            # 构建SQL
            fields = ", ".join(exam_data.keys())
            placeholders = ", ".join(["?" for _ in exam_data])
            sql = f"INSERT INTO examination_results ({fields}) VALUES ({placeholders})"
            
            # 执行插入
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(exam_data.values()))
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加检查结果成功: {exam_data['exam_id']}")
            
        except Exception as e:
            self.logger.error(f"添加检查结果失败: {str(e)}")
            raise
            
    def add_prescription(self, prescription_data: dict, prescribed_by: str):
        """添加处方"""
        try:
            # 生成处方ID
            prescription_data["prescription_id"] = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 添加处方信息
            prescription_data["prescribed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prescription_data["prescribed_by"] = prescribed_by
            prescription_data["status"] = "已开具"
            
            # 构建SQL
            fields = ", ".join(prescription_data.keys())
            placeholders = ", ".join(["?" for _ in prescription_data])
            sql = f"INSERT INTO prescriptions ({fields}) VALUES ({placeholders})"
            
            # 执行插入
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(prescription_data.values()))
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加处方成功: {prescription_data['prescription_id']}")
            
        except Exception as e:
            self.logger.error(f"添加处方失败: {str(e)}")
            raise
            
    def add_operation_record(self, operation_data: dict, created_by: str):
        """添加手术记录"""
        try:
            # 生成手术记录ID
            operation_data["operation_id"] = f"O{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 添加创建信息
            operation_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            operation_data["created_by"] = created_by
            
            # 构建SQL
            fields = ", ".join(operation_data.keys())
            placeholders = ", ".join(["?" for _ in operation_data])
            sql = f"INSERT INTO operation_records ({fields}) VALUES ({placeholders})"
            
            # 执行插入
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(operation_data.values()))
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加手术记录成功: {operation_data['operation_id']}")
            
        except Exception as e:
            self.logger.error(f"添加手术记录失败: {str(e)}")
            raise
            
    def add_attachment(self, attachment_data: dict, uploaded_by: str):
        """添加附件"""
        try:
            # 生成附件ID
            attachment_data["attachment_id"] = f"A{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 添加上传信息
            attachment_data["uploaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            attachment_data["uploaded_by"] = uploaded_by
            
            # 构建SQL
            fields = ", ".join(attachment_data.keys())
            placeholders = ", ".join(["?" for _ in attachment_data])
            sql = f"INSERT INTO record_attachments ({fields}) VALUES ({placeholders})"
            
            # 执行插入
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(attachment_data.values()))
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加附件成功: {attachment_data['attachment_id']}")
            
        except Exception as e:
            self.logger.error(f"添加附件失败: {str(e)}")
            raise
            
    def search_records(self, search_params: dict) -> list:
        """搜索病历记录"""
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if "department" in search_params:
                conditions.append("department = ?")
                params.append(search_params["department"])
                
            if "date_range" in search_params:
                start_date, end_date = search_params["date_range"]
                conditions.append("visit_date BETWEEN ? AND ?")
                params.extend([start_date, end_date])
                
            if "diagnosis" in search_params:
                conditions.append("diagnosis LIKE ?")
                params.append(f"%{search_params['diagnosis']}%")
                
            # 构建SQL
            sql = "SELECT * FROM medical_records"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                
            # 添加排序
            sort_by = search_params.get("sort_by", "created_at")
            sort_order = search_params.get("sort_order", "desc")
            sql += f" ORDER BY {sort_by} {sort_order}"
            
            # 添加分页
            page = search_params.get("page", 1)
            page_size = search_params.get("page_size", 10)
            sql += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
            
            # 执行查询
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            
            # 转换结果
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"搜索病历记录失败: {str(e)}")
            raise
            
    def export_records(self, record_ids: list, format: str = "json",
                      include_attachments: bool = False) -> str:
        """导出病历记录"""
        try:
            # 获取记录数据
            records = [self.get_record(record_id) for record_id in record_ids]
            
            # 确保导出目录存在
            export_dir = self.config.DATA_DIR / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成导出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format == "json":
                # JSON格式导出
                export_path = export_dir / f"medical_records_{timestamp}.json"
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                    
            elif format == "excel":
                # Excel格式导出
                export_path = export_dir / f"medical_records_{timestamp}.xlsx"
                
                # 转换为DataFrame
                df = pd.json_normalize(records)
                df.to_excel(export_path, index=False)
                
                if include_attachments:
                    # 创建ZIP文件
                    import shutil
                    zip_path = export_dir / f"medical_records_{timestamp}.zip"
                    shutil.make_archive(str(zip_path)[:-4], "zip", export_dir)
                    return str(zip_path)
                    
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
            self.logger.info(f"导出病历记录成功: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self.logger.error(f"导出病历记录失败: {str(e)}")
            raise
