"""医院系统配置"""

# API配置
API_CONFIG = {
    "base_url": "https://api.hospital.com/v1",
    "api_key": "YOUR_API_KEY",
    "timeout": 30,  # 请求超时时间(秒)
    "max_retries": 3,  # 最大重试次数
    "retry_delay": 1,  # 重试等待时间(秒)
}

# 医院基本信息
HOSPITAL_INFO = {
    "name": "示例医院",
    "code": "H001",
    "level": "三级甲等",
    "address": "北京市海淀区XX路XX号",
    "phone": "010-12345678",
    "website": "https://www.hospital.com"
}

# 科室配置
DEPARTMENT_CONFIG = {
    # 门诊科室
    "outpatient": [
        {
            "id": "D001",
            "name": "内科",
            "sub_departments": [
                {"id": "D001-1", "name": "呼吸内科"},
                {"id": "D001-2", "name": "心内科"},
                {"id": "D001-3", "name": "消化内科"},
                {"id": "D001-4", "name": "神经内科"}
            ]
        },
        {
            "id": "D002",
            "name": "外科",
            "sub_departments": [
                {"id": "D002-1", "name": "普外科"},
                {"id": "D002-2", "name": "骨外科"},
                {"id": "D002-3", "name": "神经外科"},
                {"id": "D002-4", "name": "心胸外科"}
            ]
        },
        {
            "id": "D003",
            "name": "妇产科",
            "sub_departments": [
                {"id": "D003-1", "name": "妇科"},
                {"id": "D003-2", "name": "产科"},
                {"id": "D003-3", "name": "计划生育科"}
            ]
        },
        {
            "id": "D004",
            "name": "儿科",
            "sub_departments": [
                {"id": "D004-1", "name": "儿科门诊"},
                {"id": "D004-2", "name": "儿科急诊"},
                {"id": "D004-3", "name": "新生儿科"}
            ]
        }
    ],
    
    # 医技科室
    "medical_tech": [
        {
            "id": "MT001",
            "name": "检验科",
            "services": [
                "血常规",
                "生化检验",
                "免疫检验",
                "微生物检验"
            ]
        },
        {
            "id": "MT002",
            "name": "影像科",
            "services": [
                "X光",
                "CT",
                "核磁共振",
                "超声"
            ]
        },
        {
            "id": "MT003",
            "name": "病理科",
            "services": [
                "活检",
                "细胞学检查",
                "冰冻切片"
            ]
        }
    ],
    
    # 急诊科室
    "emergency": [
        {
            "id": "E001",
            "name": "急诊内科",
            "priority": 1
        },
        {
            "id": "E002",
            "name": "急诊外科",
            "priority": 1
        },
        {
            "id": "E003",
            "name": "急诊妇产科",
            "priority": 2
        },
        {
            "id": "E004",
            "name": "急诊儿科",
            "priority": 2
        }
    ]
}

# 挂号配置
REGISTRATION_CONFIG = {
    "types": [
        {
            "id": "R001",
            "name": "普通门诊",
            "fee": 20,
            "limit_per_day": 50
        },
        {
            "id": "R002",
            "name": "专家门诊",
            "fee": 100,
            "limit_per_day": 20
        },
        {
            "id": "R003",
            "name": "特需门诊",
            "fee": 500,
            "limit_per_day": 10
        }
    ],
    "time_slots": [
        {"start": "08:00", "end": "12:00"},
        {"start": "14:00", "end": "17:30"}
    ],
    "max_advance_days": 14,  # 最大预约天数
    "cancel_deadline": 24  # 取消预约截止时间(小时)
}

# 住院配置
INPATIENT_CONFIG = {
    "ward_types": [
        {
            "id": "W001",
            "name": "普通病房",
            "beds_per_room": 4,
            "fee_per_day": 50
        },
        {
            "id": "W002",
            "name": "双人病房",
            "beds_per_room": 2,
            "fee_per_day": 150
        },
        {
            "id": "W003",
            "name": "单人病房",
            "beds_per_room": 1,
            "fee_per_day": 300
        },
        {
            "id": "W004",
            "name": "重症监护室",
            "beds_per_room": 1,
            "fee_per_day": 800
        }
    ],
    "admission_process": [
        "预约床位",
        "入院登记",
        "缴纳押金",
        "分配床位",
        "办理入院"
    ],
    "discharge_process": [
        "医生查房",
        "开具出院医嘱",
        "结算费用",
        "办理出院手续",
        "退还押金"
    ]
}

# 药房配置
PHARMACY_CONFIG = {
    "types": [
        {
            "id": "PH001",
            "name": "门诊药房",
            "service_hours": "08:00-17:30"
        },
        {
            "id": "PH002",
            "name": "急诊药房",
            "service_hours": "24小时"
        },
        {
            "id": "PH003",
            "name": "住院药房",
            "service_hours": "08:00-20:00"
        }
    ],
    "prescription_rules": {
        "max_days": 7,  # 最大开药天数
        "require_review": True,  # 是否需要审核
        "allow_substitution": True  # 是否允许替换药品
    }
}

# 医保配置
INSURANCE_CONFIG = {
    "supported_types": [
        {
            "id": "INS001",
            "name": "城镇职工医保",
            "reimbursement_rate": 0.8
        },
        {
            "id": "INS002",
            "name": "城乡居民医保",
            "reimbursement_rate": 0.7
        },
        {
            "id": "INS003",
            "name": "商业医疗保险",
            "reimbursement_rate": 0.6
        }
    ],
    "settlement_methods": [
        "即时结算",
        "异���结算",
        "手工报销"
    ]
}

# 检查设备配置
EQUIPMENT_CONFIG = {
    "examination": [
        {
            "id": "EQ001",
            "name": "CT机",
            "model": "GE LightSpeed VCT",
            "location": "影像中心",
            "status": "正常",
            "maintenance_cycle": 180  # 天
        },
        {
            "id": "EQ002",
            "name": "核磁共振",
            "model": "Siemens MAGNETOM Skyra",
            "location": "影像中心",
            "status": "正常",
            "maintenance_cycle": 180
        },
        {
            "id": "EQ003",
            "name": "超声诊断仪",
            "model": "飞利浦EPIQ 7",
            "location": "超声室",
            "status": "正常",
            "maintenance_cycle": 90
        }
    ],
    "operation": [
        {
            "id": "EQ101",
            "name": "手术机器人",
            "model": "达芬奇手术系统",
            "location": "手术中心",
            "status": "正常",
            "maintenance_cycle": 30
        },
        {
            "id": "EQ102",
            "name": "麻醉机",
            "model": "迈瑞WATO EX-65",
            "location": "手术���心",
            "status": "正常",
            "maintenance_cycle": 60
        }
    ]
}

# 手术室配置
OPERATION_ROOM_CONFIG = {
    "rooms": [
        {
            "id": "OR001",
            "name": "1号手术室",
            "level": "一级",
            "equipment": ["EQ101", "EQ102"]
        },
        {
            "id": "OR002",
            "name": "2号手术室",
            "level": "一级",
            "equipment": ["EQ102"]
        },
        {
            "id": "OR003",
            "name": "3号手术室",
            "level": "二级",
            "equipment": ["EQ102"]
        }
    ],
    "scheduling_rules": {
        "preparation_time": 30,  # 准备时间(分钟)
        "cleaning_time": 30,  # 清洁时间(分钟)
        "emergency_reserve": 1  # 急诊预留手术室数量
    }
}

# 系统接口配置
INTERFACE_CONFIG = {
    # HIS系统接口
    "his": {
        "url": "http://his.hospital.com/api",
        "version": "v1",
        "timeout": 30
    },
    # LIS系统接口
    "lis": {
        "url": "http://lis.hospital.com/api",
        "version": "v1",
        "timeout": 30
    },
    # PACS系统接口
    "pacs": {
        "url": "http://pacs.hospital.com/api",
        "version": "v1",
        "timeout": 60
    },
    # EMR系统接口
    "emr": {
        "url": "http://emr.hospital.com/api",
        "version": "v1",
        "timeout": 30
    }
}
