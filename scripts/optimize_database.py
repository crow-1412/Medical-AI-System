"""数据库优化脚本"""

import os
import sys
from pathlib import Path
import sqlite3

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.config import Config

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def optimize_database(db_path):
    """优化数据库"""
    try:
        print_section("开始优化数据库")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 创建索引
        print("1. 创建索引...")
        indexes = [
            # medical_records表索引
            "CREATE INDEX IF NOT EXISTS idx_records_patient ON medical_records(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_records_date ON medical_records(visit_date)",
            "CREATE INDEX IF NOT EXISTS idx_records_dept ON medical_records(department)",
            "CREATE INDEX IF NOT EXISTS idx_records_doctor ON medical_records(doctor)",
            "CREATE INDEX IF NOT EXISTS idx_records_status ON medical_records(record_status)",
            
            # examination_results表索引
            "CREATE INDEX IF NOT EXISTS idx_exam_record ON examination_results(record_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_date ON examination_results(exam_date)",
            "CREATE INDEX IF NOT EXISTS idx_exam_type ON examination_results(exam_type)",
            
            # prescriptions表索引
            "CREATE INDEX IF NOT EXISTS idx_presc_record ON prescriptions(record_id)",
            "CREATE INDEX IF NOT EXISTS idx_presc_date ON prescriptions(prescribed_at)",
            "CREATE INDEX IF NOT EXISTS idx_presc_med ON prescriptions(medication_name)",
            
            # operation_records表索引
            "CREATE INDEX IF NOT EXISTS idx_oper_record ON operation_records(record_id)",
            "CREATE INDEX IF NOT EXISTS idx_oper_date ON operation_records(operation_date)",
            "CREATE INDEX IF NOT EXISTS idx_oper_name ON operation_records(operation_name)",
            
            # record_versions表索引
            "CREATE INDEX IF NOT EXISTS idx_ver_record ON record_versions(record_id)",
            "CREATE INDEX IF NOT EXISTS idx_ver_date ON record_versions(changed_at)",
            
            # record_attachments表索引
            "CREATE INDEX IF NOT EXISTS idx_attach_record ON record_attachments(record_id)",
            "CREATE INDEX IF NOT EXISTS idx_attach_date ON record_attachments(uploaded_at)"
        ]
        
        for index in indexes:
            try:
                cursor.execute(index)
                print(f"创建索引成功: {index}")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print(f"索引已存在: {index}")
                else:
                    print(f"创建索引失败: {index}")
                    print(f"错误信息: {str(e)}")
        
        # 2. 分析表
        print("\n2. 分析表...")
        cursor.execute("ANALYZE")
        
        # 3. 整理数据库
        print("\n3. 整理数据库...")
        cursor.execute("VACUUM")
        
        conn.commit()
        print("\n数据库优化完成!")
        
    except Exception as e:
        print(f"数据库优化出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    try:
        # 确保目录存在
        Config.init_dirs()
        
        # 优化数据库
        optimize_database(Config.DB_PATH)
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
