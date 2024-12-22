from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.knowledge_agent import KnowledgeAgent
from fastapi import HTTPException

class WorkflowManager:
    def __init__(self, config):
        self.config = config
        self.agents = {}

    def initialize_agents(self, knowledge_manager):
        """初始化所有代理"""
        self.agents["report_generation"] = ReportGenerationAgent(self.config)
        
    async def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        try:
            print(f"执行工作流: {workflow_name}")
            print(f"输入数据: {input_data}")
            
            if workflow_name == "generate_report":
                # 同步执行报告生成
                result = self.agents["report_generation"].process(input_data)
                return result
            else:
                raise ValueError(f"未知的工作流: {workflow_name}")
                
        except Exception as e:
            print(f"工作流执行出错: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }