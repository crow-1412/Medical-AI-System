"""初始化数据库"""

import sqlite3
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.config import Config

def init_database():
    """初始化数据库"""
    # 确保目录存在
    Config.init_dirs()
    
    # 连接数据库
    conn = sqlite3.connect(str(Config.DB_PATH))
    cursor = conn.cursor()
    
    # 创建表
    cursor.executescript("""
    -- 医疗记录表
    CREATE TABLE IF NOT EXISTS medical_records (
        record_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        record_type TEXT NOT NULL,
        visit_date TEXT NOT NULL,
        department TEXT NOT NULL,
        doctor TEXT NOT NULL,
        chief_complaint TEXT,
        present_illness TEXT,
        past_history TEXT,
        allergic_history TEXT,
        physical_examination TEXT,
        diagnosis TEXT NOT NULL,
        treatment_plan TEXT,
        record_status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        updated_by TEXT NOT NULL
    );

    -- 检查结果表
    CREATE TABLE IF NOT EXISTS examination_results (
        exam_id TEXT PRIMARY KEY,
        record_id TEXT NOT NULL,
        exam_type TEXT NOT NULL,
        exam_date TEXT NOT NULL,
        exam_department TEXT NOT NULL,
        exam_doctor TEXT NOT NULL,
        exam_result TEXT NOT NULL,
        exam_conclusion TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES medical_records(record_id)
    );

    -- 处方表
    CREATE TABLE IF NOT EXISTS prescriptions (
        prescription_id TEXT PRIMARY KEY,
        record_id TEXT NOT NULL,
        prescription_type TEXT NOT NULL,
        medication_name TEXT NOT NULL,
        specification TEXT NOT NULL,
        dosage TEXT NOT NULL,
        frequency TEXT NOT NULL,
        duration TEXT NOT NULL,
        usage TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit TEXT NOT NULL,
        notes TEXT,
        status TEXT NOT NULL,
        prescribed_at TEXT NOT NULL,
        prescribed_by TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES medical_records(record_id)
    );

    -- 手术记录表
    CREATE TABLE IF NOT EXISTS operation_records (
        operation_id TEXT PRIMARY KEY,
        record_id TEXT NOT NULL,
        operation_name TEXT NOT NULL,
        operation_date TEXT NOT NULL,
        preoperative_diagnosis TEXT NOT NULL,
        postoperative_diagnosis TEXT NOT NULL,
        operation_level TEXT NOT NULL,
        surgeon TEXT NOT NULL,
        assistant TEXT,
        anesthesiologist TEXT,
        anesthesia_method TEXT,
        operation_description TEXT,
        blood_loss INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES medical_records(record_id)
    );

    -- 病历版本表
    CREATE TABLE IF NOT EXISTS record_versions (
        version_id TEXT PRIMARY KEY,
        record_id TEXT NOT NULL,
        version INTEGER NOT NULL,
        content TEXT NOT NULL,
        changed_fields TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        changed_by TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES medical_records(record_id)
    );

    -- 附件表
    CREATE TABLE IF NOT EXISTS record_attachments (
        attachment_id TEXT PRIMARY KEY,
        record_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        uploaded_at TEXT NOT NULL,
        uploaded_by TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES medical_records(record_id)
    );
    """)
    
    # 创建索引
    cursor.executescript("""
    -- 医疗记录表索引
    CREATE INDEX IF NOT EXISTS idx_medical_records_patient_id ON medical_records(patient_id);
    CREATE INDEX IF NOT EXISTS idx_medical_records_visit_date ON medical_records(visit_date);
    CREATE INDEX IF NOT EXISTS idx_medical_records_department ON medical_records(department);
    CREATE INDEX IF NOT EXISTS idx_medical_records_doctor ON medical_records(doctor);
    CREATE INDEX IF NOT EXISTS idx_medical_records_diagnosis ON medical_records(diagnosis);
    
    -- 检查结果表索引
    CREATE INDEX IF NOT EXISTS idx_examination_results_record_id ON examination_results(record_id);
    CREATE INDEX IF NOT EXISTS idx_examination_results_exam_date ON examination_results(exam_date);
    
    -- 处方表索引
    CREATE INDEX IF NOT EXISTS idx_prescriptions_record_id ON prescriptions(record_id);
    CREATE INDEX IF NOT EXISTS idx_prescriptions_prescribed_at ON prescriptions(prescribed_at);
    
    -- 手术记录表索引
    CREATE INDEX IF NOT EXISTS idx_operation_records_record_id ON operation_records(record_id);
    CREATE INDEX IF NOT EXISTS idx_operation_records_operation_date ON operation_records(operation_date);
    
    -- 病历版本表索引
    CREATE INDEX IF NOT EXISTS idx_record_versions_record_id ON record_versions(record_id);
    CREATE INDEX IF NOT EXISTS idx_record_versions_version ON record_versions(version);
    
    -- 附件表索引
    CREATE INDEX IF NOT EXISTS idx_record_attachments_record_id ON record_attachments(record_id);
    """)
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"数据库初始化完成: {Config.DB_PATH}")

if __name__ == "__main__":
    init_database()
