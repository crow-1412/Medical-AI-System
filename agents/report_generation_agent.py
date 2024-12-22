from typing import Dict, Any, List
from .base_agent import BaseAgent
import torch
import gc
from knowledge_base.knowledge_manager import KnowledgeManager
import re

class ReportGenerationAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config.BASE_MODEL_NAME)
        self.config = config
        self.chunk_size = config.MODEL_CONFIG.get("chunk_size", 256)
        # 初始化时加载模型
        self.load_model()
        # 添加知识库管理器
        self.knowledge_mgr = KnowledgeManager(config)
        
    def generate(self, prompt: str) -> str:
        try:
            # 确保模型已加载
            if self.model is None:
                self.load_model()
                
            self.clean_memory()
            
            # 分词处理
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.config.MODEL_CONFIG.get("max_length", 512)
            )
            
            # 确保所有输入都在正确的设备上
            device = self.model.device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 使用 torch.amp.autocast 替代 torch.cuda.amp.autocast
            with torch.inference_mode(), torch.amp.autocast('cuda'):
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    num_beams=4,  # 增加 beam search 数量
                    no_repeat_ngram_size=3,  # 避免重复
                    early_stopping=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True
                )
            
            # 解码生成的文本
            response = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            # 清理内存
            del inputs, outputs
            self.clean_memory()
            
            return response
            
        except Exception as e:
            print(f"生成报告时出错: {str(e)}")
            self.clean_memory()
            return f"生成失败: {str(e)}"
    
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
            patient_info = input_data.get("patient_info", "")
            
            # 1. 提取症状和血压
            symptoms = self._extract_symptoms(patient_info)
            bp_match = re.search(r'血压(\d+/\d+)mmHg', patient_info)
            bp = bp_match.group(1) if bp_match else "120/80"  # 默认正常血压
            
            # 2. 分析症状关联，传入血压值
            symptoms_analysis = await self.knowledge_mgr.analyze_symptoms(symptoms, bp)
            
            # 3. 从知识库检索相关内容
            relevant_docs = await self.knowledge_mgr.search(
                query=patient_info,
                k=5
            )
            
            # 4. 生成初步诊断
            diagnosis = self._generate_diagnosis(symptoms_analysis)
            
            # 5. 生成治疗方案
            treatment_plan = await self.knowledge_mgr.generate_treatment_plan(
                diagnosis,
                symptoms
            )
            
            # 6. 构建完整提示
            context = self._build_context(relevant_docs)
            prompt = self._build_prompt(
                patient_info,
                context,
                symptoms_analysis,
                diagnosis,
                treatment_plan
            )
            
            # 7. 生成最终报告
            report = self.generate(prompt)
            
            return {
                "status": "success",
                "data": {
                    "report": report,
                    "analysis": symptoms_analysis,
                    "treatment_plan": treatment_plan
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
    
    def _extract_symptoms(self, patient_info: str) -> list:
        """从患者信息中提取症状"""
        symptoms = []
        # 定义常见症状关键词
        symptom_keywords = [
            "头痛", "眩晕", "乏力", "心悸", "胸闷", "呼吸急促",
            "咳嗽", "发热", "腹痛", "恶心", "呕吐", "腹泻",
            "关节痛", "肌肉酸痛", "失眠", "食欲不振"
        ]
        
        for symptom in symptom_keywords:
            if symptom in patient_info:
                symptoms.append(symptom)
                
        # 提取血压值
        import re
        bp_match = re.search(r'血压(\d+/\d+)mmHg', patient_info)
        if bp_match:
            symptoms.append(f"血压{bp_match.group(1)}mmHg")
            
        return symptoms
    
    def _generate_diagnosis(self, symptoms_analysis: dict) -> str:
        """根据症状分析生成诊断"""
        try:
            primary_symptoms = symptoms_analysis.get("primary_symptoms", [])
            risk_level = symptoms_analysis.get("risk_level", "")
            related_diseases = symptoms_analysis.get("related_diseases", [])
            
            diagnosis = []
            
            # 添加主要症状
            if primary_symptoms:
                diagnosis.append(f"主要症状：{', '.join(primary_symptoms)}")
            
            # 添加风险等级
            if risk_level:
                diagnosis.append(f"风险等级：{risk_level}")
            
            # 添加相关疾病
            if related_diseases:
                diagnosis.append(f"相关疾病：{', '.join(related_diseases)}")
            
            return "\n".join(diagnosis)
            
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
                     treatment_plan: dict) -> str:
        """构建完整的提示"""
        return f"""请根据以下信息生成一份专业的医疗报告：

患者信息：
{patient_info}

症状分析：
主要症状：{', '.join(symptoms_analysis['primary_symptoms'])}
次要症状：{', '.join(symptoms_analysis['secondary_symptoms'])}
风险等级：{symptoms_analysis['risk_level']}
相关疾病：{', '.join(symptoms_analysis['related_diseases'])}

诊断建议：
{diagnosis}

治疗方案：
1. 药物治疗：
{chr(10).join(f'- {med}' for med in treatment_plan['medications'])}

2. 生活方式调整：
{chr(10).join(f'- {change}' for change in treatment_plan['lifestyle_changes'])}

3. 随访计划：
{treatment_plan['follow_up']}

4. 注意事项：
{chr(10).join(f'- {precaution}' for precaution in treatment_plan['precautions'])}

相关医学知识：
{context}

请生成一份结构完整、专业规范的医疗报告，包括：
1. 患者基本情况
2. 现病史和症状描述
3. 体格检查结果
4. 初步诊断和风险评估
5. 治疗方案和建议
6. 随访计划和注意事项
"""