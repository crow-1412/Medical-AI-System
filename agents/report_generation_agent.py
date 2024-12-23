from typing import Dict, Any, List, Tuple
from .base_agent import BaseAgent
import torch
import gc
from knowledge_base.knowledge_manager import KnowledgeManager
import re
from pathlib import Path

class ReportGenerationAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config.BASE_MODEL_NAME)
        self.config = config
        self.chunk_size = config.MODEL_CONFIG.get("chunk_size", 256)
        # 初始化时加载模型
        self.load_model()
        # 添加知识库管理器
        self.knowledge_mgr = KnowledgeManager(config)
        # 加载微调模型
        self._load_finetuned_model()
        
    def _load_finetuned_model(self):
        """加载微调后的模型"""
        try:
            # 检查是否存在微调模型
            lora_path = Path(self.config.STORAGE_PATHS["model_cache"]) / "lora_weights"
            if lora_path.exists():
                print("加载 LoRA 微调模型...")
                from peft import PeftModel, PeftConfig
                
                # 加载 LoRA 配置
                config = PeftConfig.from_pretrained(str(lora_path))
                
                # 将基础模型转换为 PEFT 模型
                self.model = PeftModel.from_pretrained(
                    self.model,
                    str(lora_path),
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                
                print("LoRA 模型加载完成")
            else:
                print("未找到微调模型，将使用基础模型")
                
        except Exception as e:
            print(f"加载微调模型失败: {str(e)}")
            print("将使用基础模型继续")
            
    def generate(self, prompt: str) -> str:
        """生成报告内容"""
        try:
            # 优化生成参数
            generation_config = {
                "max_length": 512,
                "min_length": 100,
                "num_beams": 1,
                "do_sample": True,
                "top_p": 0.9,
                "temperature": 0.8,
                "repetition_penalty": 1.1,
                "length_penalty": 1.0,
                "early_stopping": True,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            # 优化输入处理
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=256
            )
            inputs = inputs.to(self.device)
            
            # 使用torch.cuda.amp.autocast()进行混合精度计算
            with torch.cuda.amp.autocast():
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        **generation_config
                    )
            
            # 解码输出
            report = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 立即清理显存
            del outputs
            del inputs
            torch.cuda.empty_cache()
            gc.collect()
            
            return report
            
        except Exception as e:
            print(f"生成报告失败: {str(e)}")
            return "生成报告时发生错误"
            
    def _build_dynamic_prompt(self, patient_details: Dict[str, Any],
                            symptoms: Dict[str, List[str]],
                            vitals: Dict[str, str],
                            context: str,
                            symptoms_analysis: dict,
                            diagnosis: str,
                            treatment_plan: dict,
                            report_type: str) -> str:
        """构建动态提示词"""
        
        # 构建简明的提示模板
        template = f"""生成{report_type}：

患者：{patient_details.get('gender', '')}，{patient_details.get('age', '')}岁
主诉：{patient_details.get('original_text', '')}

症状：{'、'.join([f"{system}({', '.join(symptoms)})" for system, symptoms in symptoms.items()]) if symptoms else '无明显症状'}

体征：{'、'.join([f"{name}: {value}" for name, value in vitals.items()]) if vitals else '未见异常'}

诊断：{diagnosis if diagnosis else '待进一步检查'}

治疗：
1. {', '.join(treatment_plan.get('medications', ['无特殊用药']))}
2. {', '.join(treatment_plan.get('lifestyle_changes', ['保持良好作息']))}
3. {treatment_plan.get('follow_up', '定期复查')}

注意：{', '.join(treatment_plan.get('precautions', ['遵医嘱']))}

请生成简明扼要的{report_type}。"""

        return template
    
    def clean_memory(self):
        """清理 GPU 内存"""
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                with torch.cuda.device(i):
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
            gc.collect()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            print("开始处理输入数据...")
            patient_info = input_data.get("patient_info", "")
            report_type = input_data.get("report_type", "初步诊断报告")
            
            # 1. 提取患者基本信息
            print("提取患者基本信息...")
            patient_details = self._extract_patient_details(patient_info)
            
            # 2. 提取症状和体征
            print("提取症状和体征...")
            symptoms, vitals = self._extract_symptoms_and_vitals(patient_info)
            
            # 3. 从知识库检索相关内容
            print("检索知识库...")
            # 构建更精确的查询
            knowledge_query = f"""
            症状：{', '.join([sym for syms in symptoms.values() for sym in syms])}
            体征：{', '.join([f'{k}:{v}' for k,v in vitals.items()])}
            患者：{patient_details.get('gender', '')} {patient_details.get('age', '')}岁
            """
            relevant_docs = await self.knowledge_mgr.search(knowledge_query, k=5)
            
            # 4. 分析症状关联和风险评估
            print("分析症状和风险...")
            symptoms_analysis = await self.knowledge_mgr.analyze_symptoms(
                symptoms,
                vitals.get("blood_pressure", "120/80"),
                patient_details,
                relevant_docs  # 传入知识库检索结果
            )
            
            # 5. 生成初步诊断
            print("生成诊断...")
            diagnosis = self._generate_diagnosis(
                symptoms_analysis,
                symptoms,
                vitals,
                patient_details,
                relevant_docs  # 传入知识库检索结果
            )
            
            # 6. 生成个性化治疗方案
            print("生成治疗方案...")
            treatment_plan = await self.knowledge_mgr.generate_treatment_plan(
                diagnosis,
                symptoms,
                patient_details,
                relevant_docs  # 传入知识库检索结果
            )
            
            # 7. 使用微调后的模型生成报告
            print("使用微调模型生成报告...")
            context = self._build_context(relevant_docs)
            prompt = self._build_dynamic_prompt(
                patient_details,
                symptoms,
                vitals,
                context,
                symptoms_analysis,
                diagnosis,
                treatment_plan,
                report_type
            )
            
            report = self.generate(prompt)
            
            return {
                "status": "success",
                "data": {
                    "report": report,
                    "analysis": symptoms_analysis,
                    "treatment_plan": treatment_plan,
                    "knowledge_sources": [doc.get("title", "") for doc in relevant_docs]
                }
            }
            
        except Exception as e:
            print(f"处理报告生成请求时出错: {str(e)}")
            return {
                "status": "error",
                "data": {
                    "report": f"生成报告失败: {str(e)}",
                    "error": str(e)
                }
            }
    
    def _extract_patient_details(self, patient_info: str) -> Dict[str, Any]:
        """提取患者基本信息"""
        details = {}
        
        # 提取性别
        if "男" in patient_info:
            details["gender"] = "男"
        elif "女" in patient_info:
            details["gender"] = "女"
            
        # 提取年龄
        age_match = re.search(r'(\d+)岁', patient_info)
        if age_match:
            details["age"] = int(age_match.group(1))
            
        # 提取其他基本信息
        details["original_text"] = patient_info
        
        return details
    
    def _extract_symptoms_and_vitals(self, patient_info: str) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        """提取症状和生命体征"""
        symptoms = {}
        vitals = {}
        
        # 系统性症状提取
        symptom_patterns = {
            "全身��状": [
                (r'发热(\d+\.?\d*)?度?', "发热"),
                (r'乏力', "乏力"),
                (r'疲劳', "疲劳"),
                (r'体重(减轻|增加)(\d+\.?\d*)?k?g?', "体重改变")
            ],
            "心血管系统": [
                (r'胸痛', "胸痛"),
                (r'心悸', "心悸"),
                (r'气短', "气短"),
                (r'水肿', "水肿")
            ],
            "呼吸系统": [
                (r'咳嗽', "咳嗽"),
                (r'咳痰', "咳痰"),
                (r'呼吸困难', "呼吸困难"),
                (r'胸闷', "胸闷")
            ]
            # 可以添加更多系统的症状
        }
        
        # 提取症状
        for system, patterns in symptom_patterns.items():
            system_symptoms = []
            for pattern, symptom_name in patterns:
                if re.search(pattern, patient_info):
                    system_symptoms.append(symptom_name)
            if system_symptoms:
                symptoms[system] = system_symptoms
        
        # 提取生命体征
        vitals_patterns = {
            "blood_pressure": r'血压(\d+/\d+)mmHg',
            "temperature": r'体温(\d+\.?\d*)℃',
            "pulse": r'脉搏(\d+)次/分',
            "breathing": r'呼吸(\d+)次/分',
            "blood_sugar": r'血糖(\d+\.?\d*)mmol/L'
        }
        
        for vital_name, pattern in vitals_patterns.items():
            match = re.search(pattern, patient_info)
            if match:
                vitals[vital_name] = match.group(1)
        
        return symptoms, vitals
    
    def _build_specific_query(self, patient_details: Dict[str, Any], 
                            symptoms: Dict[str, List[str]], 
                            vitals: Dict[str, str]) -> str:
        """构建特定的知识库查询"""
        query_parts = []
        
        # 添加患者基本信息
        if patient_details.get("gender"):
            query_parts.append(f"{patient_details['gender']}性")
        if patient_details.get("age"):
            query_parts.append(f"{patient_details['age']}岁")
            
        # 添加主要症状
        for system, system_symptoms in symptoms.items():
            query_parts.extend(system_symptoms)
            
        # 添加关键生命体征
        if vitals.get("blood_pressure"):
            query_parts.append(f"血压{vitals['blood_pressure']}")
        if vitals.get("temperature"):
            query_parts.append(f"体温{vitals['temperature']}")
            
        return " ".join(query_parts)
    
    def _generate_diagnosis(self, symptoms_analysis: dict, found_symptoms: dict) -> str:
        """根据症状分析生成诊断"""
        try:
            diagnosis_parts = []
            
            # 添加主要症状
            if symptoms_analysis.get("primary_symptoms"):
                diagnosis_parts.append(f"主要症状：{', '.join(symptoms_analysis['primary_symptoms'])}")
            
            # 按系统添加症状
            for system, symptoms in found_symptoms.items():
                if symptoms:
                    diagnosis_parts.append(f"{system}表现：{', '.join(symptoms)}")
            
            # 添加风险等级
            risk_level = symptoms_analysis.get("risk_level", "")
            if risk_level:
                diagnosis_parts.append(f"风险等级：{risk_level}")
            
            # 添加相关疾病
            related_diseases = symptoms_analysis.get("related_diseases", [])
            if related_diseases:
                diagnosis_parts.append(f"相关疾病：{', '.join(related_diseases)}")
            
            return "\n".join(diagnosis_parts)
            
        except Exception as e:
            print(f"生成诊断失败: {str(e)}")
            return "无法生成诊断信息"
    
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """构建上下文信息"""
        context_parts = []
        for doc in docs:
            if isinstance(doc, dict):
                title = doc.get("title", "")
                content = doc.get("content", "")
                if title and content:
                    context_parts.append(f"标题：{title}\n内容：{content}")
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, patient_info: str, context: str, 
                     symptoms_analysis: dict, diagnosis: str,
                     treatment_plan: dict, report_type: str) -> str:
        """构建完整的提示"""
        
        # 根据报告类型选择模板
        if report_type == "初步诊断报告":
            template = """请根据以下信息生成一份专业的初步诊断报告：

患者信息：
{patient_info}

症状分析：
{diagnosis}

建议治疗方案：
1. 药物治疗：
{medications}

2. 生活方式调整：
{lifestyle}

3. 随访计划：
{follow_up}

4. 注意事项：
{precautions}

相关医学知识：
{context}

请生成一份结构完整、专业规范的初步诊断报告，包括：
1. 患者基本情况
2. 现病史和症状描述
3. 体格检查结果
4. 初步诊断和风险评估
5. 治疗方案和建议
6. 随访计划和注意事项"""
            
        elif report_type == "住院记录":
            template = """请根据以下信息生成一份专业的住院记录：

患者信息：
{patient_info}

入院诊断：
{diagnosis}

治疗方案：
1. 药物治疗：
{medications}

2. 护理要点：
{lifestyle}

3. 检查计划：
{follow_up}

4. 注意事项：
{precautions}

相关医学知识：
{context}

请生成一份结构完整、专业规范的住院记录，包括：
1. 患者基本信息
2. 入院诊断
3. 治疗计划
4. 护理要点
5. 检查安排
6. 注意事项"""
            
        else:  # 手术记录
            template = """请根据以下信息生成一份专业的手术记录：

患者信息：
{patient_info}

手术诊断：
{diagnosis}

手术方案：
1. 手术准备：
{medications}

2. 手术要点：
{lifestyle}

3. 术后观察：
{follow_up}

4. 注意事项：
{precautions}

相关医学知识：
{context}

请生成一份��构完整、专业规范的手术记录，包括：
1. 患者基本信息
2. 手术诊断
3. 手术方案
4. 手术过程
5. 术后观察
6. 注意事项"""
        
        # 格式化模板
        return template.format(
            patient_info=patient_info,
            diagnosis=diagnosis,
            medications="\n".join(f"- {med}" for med in treatment_plan['medications']),
            lifestyle="\n".join(f"- {change}" for change in treatment_plan['lifestyle_changes']),
            follow_up=treatment_plan['follow_up'],
            precautions="\n".join(f"- {precaution}" for precaution in treatment_plan['precautions']),
            context=context
        )