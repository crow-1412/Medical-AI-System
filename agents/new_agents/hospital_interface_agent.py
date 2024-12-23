import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from config.config import Config

class HospitalInterfaceAgent:
    """医院系统接口代理"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self._setup_logging()
        self._setup_api_config()
        
    def _setup_logging(self):
        """设置日志记录"""
        log_dir = Path(self.config.STORAGE_PATHS["logs"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"hospital_interface_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("HospitalInterface")
        
    def _setup_api_config(self):
        """设置API配置"""
        self.base_url = self.config.HOSPITAL_CONFIG["api_base_url"]
        self.api_key = self.config.HOSPITAL_CONFIG["api_key"]
        self.timeout = self.config.HOSPITAL_CONFIG["timeout"]
        self.max_retries = self.config.HOSPITAL_CONFIG["max_retries"]
        
    async def initialize(self):
        """初始化会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            self.logger.info("医院接口会话已初始化")
            
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("医院接口会话已关闭")
            
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送请求并处理响应"""
        if not self.session:
            await self.initialize()
            
        url = f"{self.base_url}{endpoint}"
        retries = 0
        
        while retries < self.max_retries:
            try:
                async with self.session.request(method, url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise ValueError("API认证失败")
                    elif response.status == 404:
                        raise ValueError(f"未找到资源: {endpoint}")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"请求失败: {response.status} - {error_text}")
                        if retries < self.max_retries - 1:
                            retries += 1
                            await asyncio.sleep(2 ** retries)  # 指数退避
                            continue
                        raise ValueError(f"请求失败: {response.status}")
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"请求出错: {str(e)}")
                if retries < self.max_retries - 1:
                    retries += 1
                    await asyncio.sleep(2 ** retries)
                    continue
                raise
                
        raise ValueError("超过最大重试次数")
        
    async def get_patient_info(self, patient_id: str) -> Dict[str, Any]:
        """获取患者信息"""
        try:
            response = await self._make_request("GET", f"/patients/{patient_id}")
            return response
        except Exception as e:
            self.logger.error(f"获取患者信息失败: {str(e)}")
            raise
            
    async def update_medical_record(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新医疗记录"""
        try:
            response = await self._make_request("PUT", f"/medical_records/{record_id}", data)
            return response
        except Exception as e:
            self.logger.error(f"更新医疗记录失败: {str(e)}")
            raise
            
    async def get_department_info(self, department_id: str) -> Dict[str, Any]:
        """获取科室信息"""
        try:
            response = await self._make_request("GET", f"/departments/{department_id}")
            return response
        except Exception as e:
            self.logger.error(f"获取科室信息失败: {str(e)}")
            raise
            
    async def schedule_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """预约挂号"""
        try:
            response = await self._make_request("POST", "/appointments", appointment_data)
            return response
        except Exception as e:
            self.logger.error(f"预约挂号失败: {str(e)}")
            raise
            
    async def get_doctor_schedule(self, doctor_id: str, date: str) -> List[Dict[str, Any]]:
        """获取医生排班"""
        try:
            response = await self._make_request("GET", f"/doctors/{doctor_id}/schedule?date={date}")
            return response
        except Exception as e:
            self.logger.error(f"获取医生排班失败: {str(e)}")
            raise
            
    async def submit_examination_results(self, examination_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交检查结果"""
        try:
            response = await self._make_request("POST", "/examinations", examination_data)
            return response
        except Exception as e:
            self.logger.error(f"提交检查结果失败: {str(e)}")
            raise
            
    async def get_medication_info(self, medication_id: str) -> Dict[str, Any]:
        """获取药品信息"""
        try:
            response = await self._make_request("GET", f"/medications/{medication_id}")
            return response
        except Exception as e:
            self.logger.error(f"获取药品信息失败: {str(e)}")
            raise
            
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建处方"""
        try:
            response = await self._make_request("POST", "/prescriptions", prescription_data)
            return response
        except Exception as e:
            self.logger.error(f"创建处方失败: {str(e)}")
            raise
            
    async def get_insurance_info(self, patient_id: str) -> Dict[str, Any]:
        """获取医保信息"""
        try:
            response = await self._make_request("GET", f"/insurance/{patient_id}")
            return response
        except Exception as e:
            self.logger.error(f"获取医保信息失败: {str(e)}")
            raise
            
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理支付"""
        try:
            response = await self._make_request("POST", "/payments", payment_data)
            return response
        except Exception as e:
            self.logger.error(f"处理支付失败: {str(e)}")
            raise
            
    async def check_bed_availability(self, department_id: str) -> Dict[str, Any]:
        """查询床位可用情况"""
        try:
            response = await self._make_request("GET", f"/beds/availability/{department_id}")
            return response
        except Exception as e:
            self.logger.error(f"查询床位失败: {str(e)}")
            raise
            
    async def register_admission(self, admission_data: Dict[str, Any]) -> Dict[str, Any]:
        """登记入院"""
        try:
            response = await self._make_request("POST", "/admissions", admission_data)
            return response
        except Exception as e:
            self.logger.error(f"登记入院失败: {str(e)}")
            raise
            
    async def process_discharge(self, patient_id: str, discharge_data: Dict[str, Any]) -> Dict[str, Any]:
        """办理出院"""
        try:
            response = await self._make_request("POST", f"/discharges/{patient_id}", discharge_data)
            return response
        except Exception as e:
            self.logger.error(f"办理出院失败: {str(e)}")
            raise
            
    async def get_operation_room_schedule(self, date: str) -> List[Dict[str, Any]]:
        """获取手术室排期"""
        try:
            response = await self._make_request("GET", f"/operation_rooms/schedule?date={date}")
            return response
        except Exception as e:
            self.logger.error(f"获取手术室排期失败: {str(e)}")
            raise
            
    async def schedule_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """安排手术"""
        try:
            response = await self._make_request("POST", "/operations", operation_data)
            return response
        except Exception as e:
            self.logger.error(f"安排手术失败: {str(e)}")
            raise
            
    async def get_examination_equipment_schedule(self, equipment_id: str, date: str) -> List[Dict[str, Any]]:
        """获取检查设备排期"""
        try:
            response = await self._make_request(
                "GET", 
                f"/examination_equipment/{equipment_id}/schedule?date={date}"
            )
            return response
        except Exception as e:
            self.logger.error(f"获取检查设备排期失败: {str(e)}")
            raise
            
    async def schedule_examination(self, examination_data: Dict[str, Any]) -> Dict[str, Any]:
        """预约检查"""
        try:
            response = await self._make_request("POST", "/examination_appointments", examination_data)
            return response
        except Exception as e:
            self.logger.error(f"预约检查失败: {str(e)}")
            raise
