import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.new_agents.hospital_interface_agent import HospitalInterfaceAgent
from config.config import Config

async def main():
    """主函数"""
    try:
        # 创建医院接口代理
        agent = HospitalInterfaceAgent(Config)
        
        # 初始化连接
        await agent.initialize()
        
        try:
            # 1. 获取患者信息
            print("\n1. 获取患者信息")
            patient_info = await agent.get_patient_info("P123456")
            print(f"患者信息: {patient_info}")
            
            # 2. 获取科室信息
            print("\n2. 获取科室信息")
            department_info = await agent.get_department_info("D001")
            print(f"科室信息: {department_info}")
            
            # 3. 查询医生排班
            print("\n3. 查询医生排班")
            today = datetime.now().strftime("%Y-%m-%d")
            schedule = await agent.get_doctor_schedule("DR001", today)
            print(f"医生排班: {schedule}")
            
            # 4. 预约挂号
            print("\n4. 预约挂号")
            appointment_data = {
                "patient_id": "P123456",
                "doctor_id": "DR001",
                "department_id": "D001",
                "appointment_time": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:00"),
                "appointment_type": "普通门诊",
                "symptoms": "发热、咳嗽"
            }
            appointment_result = await agent.schedule_appointment(appointment_data)
            print(f"预约结果: {appointment_result}")
            
            # 5. 查询床位
            print("\n5. 查询床位")
            bed_info = await agent.check_bed_availability("D001")
            print(f"床位信息: {bed_info}")
            
            # 6. 创建处方
            print("\n6. 创建处方")
            prescription_data = {
                "patient_id": "P123456",
                "doctor_id": "DR001",
                "diagnosis": "上呼吸道感染",
                "medications": [
                    {
                        "medication_id": "M001",
                        "name": "布洛芬缓释胶囊",
                        "specification": "0.3g",
                        "usage": "口服",
                        "frequency": "每12小时一次",
                        "duration": "3天",
                        "quantity": 6
                    },
                    {
                        "medication_id": "M002",
                        "name": "氯雷他定片",
                        "specification": "10mg",
                        "usage": "口服",
                        "frequency": "每日一次",
                        "duration": "3天",
                        "quantity": 3
                    }
                ],
                "notes": "饭后服用"
            }
            prescription_result = await agent.create_prescription(prescription_data)
            print(f"处方创建结果: {prescription_result}")
            
            # 7. 查询医保信息
            print("\n7. 查询医保信息")
            insurance_info = await agent.get_insurance_info("P123456")
            print(f"医保信息: {insurance_info}")
            
            # 8. 处理支付
            print("\n8. 处理支付")
            payment_data = {
                "patient_id": "P123456",
                "prescription_id": prescription_result["prescription_id"],
                "amount": 89.5,
                "payment_method": "医保",
                "insurance_type": "城镇职工医保"
            }
            payment_result = await agent.process_payment(payment_data)
            print(f"支付结果: {payment_result}")
            
            # 9. 预约检查
            print("\n9. 预约检查")
            examination_data = {
                "patient_id": "P123456",
                "doctor_id": "DR001",
                "examination_type": "心电图",
                "equipment_id": "E001",
                "appointment_time": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:00:00"),
                "notes": "空腹检查"
            }
            examination_result = await agent.schedule_examination(examination_data)
            print(f"检查预约结果: {examination_result}")
            
            # 10. 提交检查结果
            print("\n10. 提交检查结果")
            results_data = {
                "examination_id": examination_result["examination_id"],
                "patient_id": "P123456",
                "doctor_id": "DR001",
                "examination_type": "心电图",
                "results": "窦性心律，心率75次/分，各导联ST-T正常。",
                "conclusion": "心电图未见明显异常。",
                "recommendations": "建议定期复查。"
            }
            submit_result = await agent.submit_examination_results(results_data)
            print(f"检查结果提交: {submit_result}")
            
        finally:
            # 关闭连接
            await agent.close()
            
    except Exception as e:
        print(f"运行出错: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
