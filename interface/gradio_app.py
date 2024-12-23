import gradio as gr
from config.config import Config
from knowledge_base.knowledge_manager import KnowledgeManager

async def create_gradio_interface():
    """创建Gradio界面"""
    
    # 初始化知识库管理器
    knowledge_manager = KnowledgeManager(Config)
    
    # 创建界面
    with gr.Blocks(title="医疗AI助手") as demo:
        gr.Markdown("# 医疗AI助手")
        
        with gr.Row():
            with gr.Column():
                # 输入区域
                patient_info = gr.Textbox(
                    label="患者信息",
                    placeholder="请输入患者的基本信息，如：患者，女，35岁，咳嗽，发热三天，体温38.5°C"
                )
                
                report_type = gr.Radio(
                    choices=["初步诊断报告", "详细检查建议", "治疗方案"],
                    label="报告类型",
                    value="初步诊断报告"
                )
                
                submit_btn = gr.Button("生成报告")
                
            with gr.Column():
                # 输出区域
                output = gr.Textbox(
                    label="医疗报告",
                    lines=10
                )
                
        # 处理函数
        async def generate_report(info: str, report_type: str) -> str:
            try:
                # 从知识库检索相关信息
                results = await knowledge_manager.search(info)
                
                if not results:
                    return "抱歉，无法根据提供的信息生成报告。请提供更详细的患者信息。"
                
                # 根据报告类型生成不同的报告
                if report_type == "初步诊断报告":
                    report = "初步诊断报告\n\n"
                    report += f"患者信息：{info}\n\n"
                    report += "可能的相关疾病：\n"
                    for result in results:
                        if "disease" in result:
                            report += f"- {result['disease']}\n"
                            if "symptoms" in result:
                                report += f"  典型症状：{', '.join(result['symptoms'])}\n"
                            report += "\n"
                            
                elif report_type == "详细检查建议":
                    report = "检查建议\n\n"
                    report += f"基于患者情况：{info}\n\n"
                    report += "建议进行以下检查：\n"
                    for result in results:
                        if "treatments" in result and "precautions" in result["treatments"]:
                            report += f"- {result['treatments']['precautions']}\n"
                            
                else:  # 治疗方案
                    report = "治疗方案建议\n\n"
                    report += f"针对患者情况：{info}\n\n"
                    for result in results:
                        if "treatments" in result:
                            treatments = result["treatments"]
                            if "medications" in treatments:
                                report += f"药物建议：\n- {', '.join(treatments['medications'])}\n\n"
                            if "lifestyle" in treatments:
                                report += f"生活建议：\n- {', '.join(treatments['lifestyle'])}\n"
                
                return report
                
            except Exception as e:
                print(f"生成报告时出错: {str(e)}")
                return "生成报告时发生错误，请稍后重试。"
        
        # 绑定事件
        submit_btn.click(
            fn=generate_report,
            inputs=[patient_info, report_type],
            outputs=output
        )
        
    return demo