from typing import Dict, Any
from .base_agent import BaseAgent
import torch
import gc
from knowledge_base.knowledge_manager import KnowledgeManager

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
            
            # 1. 提取症状
            symptoms = self._extract_symptoms(patient_info)
            
            # 2. 分析症状关联
            symptoms_analysis = await self.knowledge_mgr.analyze_symptoms(symptoms)
            
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
                "message": str(e)
            } 