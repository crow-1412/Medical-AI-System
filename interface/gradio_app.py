import gradio as gr
import asyncio
import torch
import gc
from workflows.workflow_manager import WorkflowManager
from knowledge_base.knowledge_manager import KnowledgeManager
from config.config import Config
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import bitsandbytes as bnb
import socket

class BaseAgent:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        try:
            # 清理现有内存
            clean_gpu_memory()
            
            # 配置 8-bit 量化
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False
            )
            
            # 设置模型加载参数
            load_config = {
                "device_map": "auto",          # 自动设备映射
                "max_memory": {0: "15GB"},     # 限制GPU内存使用
                "offload_folder": "/root/autodl-tmp/offload",  # 模型权重卸���目录
                "quantization_config": quantization_config,    # 8-bit 量化
                "load_in_8bit": True,          # 启用 8-bit 量化
                "trust_remote_code": True,
                "use_auth_token": False,
                "torch_dtype": torch.float16,   # 使用半精度
                "low_cpu_mem_usage": True      # 低内存加载
            }
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                use_fast=True  # 使用快速分词器
            )
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                **load_config
            )
            
            # 使用 bitsandbytes 进行额外优化
            for param in self.model.parameters():
                param.data = param.data.to(torch.int8)
            
            # 设置生成参数
            self.model.config.use_cache = True  # 启用 KV 缓存
            self.model.generation_config.max_new_tokens = 256  # 减小生成长度
            self.model.generation_config.temperature = 0.7
            self.model.generation_config.top_p = 0.9
            self.model.generation_config.do_sample = True
            
            # 确保有 pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            # 启用梯度检查点
            self.model.gradient_checkpointing_enable()
            
            # 清理缓存
            clean_gpu_memory()
                
        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            raise e

class MedicalReportGenerator:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MedicalReportGenerator, cls).__new__(cls)
            cls._instance.knowledge_mgr = None
            cls._instance.workflow_mgr = None
            cls._instance._is_initialized = False
        return cls._instance
    
    async def initialize(self):
        async with self._lock:  # 使用锁来确保并发安全
            if not self._is_initialized:
                try:
                    if torch.cuda.is_available():
                        clean_gpu_memory()
                        torch.cuda.set_per_process_memory_fraction(0.6)
                    
                    # 初始化知识库管理器
                    self.knowledge_mgr = KnowledgeManager(config=Config)
                    print("开始初始化知识库...")
                    await self.knowledge_mgr.initialize()
                    print("知识库初始化完成")
                    
                    # 初始化工作流管理器
                    self.workflow_mgr = WorkflowManager(Config)
                    self.workflow_mgr.initialize_agents(self.knowledge_mgr)
                    
                    self._is_initialized = True
                    print("系统初始化完成")
                    
                except Exception as e:
                    print(f"初始化失败: {str(e)}")
                    raise

    async def generate_report(self, patient_info: str, report_type: str = "初步诊断报告") -> str:
        """异步版本的报告生成函数"""
        try:
            if not self._is_initialized:
                await self.initialize()
            
            result = await self.workflow_mgr.execute_workflow(
                "generate_report",
                {
                    "patient_info": patient_info,
                    "report_type": report_type
                }
            )
            
            if isinstance(result, dict):
                if "data" in result and isinstance(result["data"], dict):
                    return result["data"].get("report", "生成报告失败")
                elif "report" in result:
                    return result["report"]
            
            return str(result)
            
        except Exception as e:
            print(f"生成报告时出错: {str(e)}")
            return f"生成报告失败: {str(e)}"

# 创建全局单例实例
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = MedicalReportGenerator()
    return _generator

def create_gradio_interface():
    # 使用全局单例实例
    generator = get_generator()
    
    # 设置界面主题和样式
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="gray",
        neutral_hue="gray"
    )
    
    with gr.Blocks(theme=theme, css="footer {display: none}") as demo:
        gr.Markdown("# 医疗报告生成系统")
        gr.Markdown("输入患者信息，自动生成规范的医疗报告。")
        
        with gr.Row():
            with gr.Column(scale=1):
                patient_info = gr.Textbox(
                    label="患者信息",
                    placeholder="请输入患者的基本信息、症状等...",
                    lines=5
                )
                report_type = gr.Dropdown(
                    choices=["初步诊断报告", "住院记录", "手术记录"],
                    label="报告类型",
                    value="初步诊断报告"
                )
                submit_btn = gr.Button("生成报告", variant="primary")
            
            with gr.Column(scale=1):
                output = gr.Textbox(
                    label="生成的报告",
                    lines=10,
                    show_copy_button=True
                )
        
        # 添加示例
        gr.Examples(
            examples=[
                ["患者，男，45岁，血压160/100mmHg，头痛、眩晕", "初步诊断报告"],
                ["患者，女，35岁，咳嗽、发热三天，体温38.5℃", "初步诊断报告"]
            ],
            inputs=[patient_info, report_type]
        )
        
        # 绑定生成函数并设置队列
        submit_btn.click(
            fn=lambda x, y: asyncio.run(generator.generate_report(x, y)),
            inputs=[patient_info, report_type],
            outputs=output,
            api_name="generate",
            queue=True
        )
    
    return demo

def clean_gpu_memory():
    if torch.cuda.is_available():
        # 清理所有 GPU 的缓存
        for i in range(torch.cuda.device_count()):
            with torch.cuda.device(i):
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
        
        # 清理 Python 对象
        gc.collect()

if __name__ == "__main__":
    # 设置 CUDA 环境变量
    import os
    import socket
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True,max_split_size_mb:256'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'
    
    # 设置 bitsandbytes 参数
    os.environ['BITSANDBYTES_NOWELCOME'] = '1'
    
    # 清理环境
    clean_gpu_memory()
    
    # 获取服务器IP地址
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"\n服务器信息:")
    print(f"主机名: {hostname}")
    print(f"容器内部IP: {ip_address}")
    print(f"注意: 这是Docker容器的内部地址，无法直接访问")
    print(f"请在AutoDL控制台中:")
    print(f"1. 找到'开放端口'或'SSH&Jupyter'选项卡")
    print(f"2. 将端口 7860 映射到公网")
    print(f"3. 使用AutoDL提供的访问地址访问\n")
    
    # 获取全局生成器实例并初始化
    generator = get_generator()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generator.initialize())
    
    # 创建并启动 Gradio 界面
    demo = create_gradio_interface()
    
    print("\n正在启动服务器...")
    print("如果长时间未显示'Running'信息，请检查:")
    print("1. 端口 7860 是否已被占用")
    print("2. 是否有足够的系统资源")
    print("3. 在AutoDL控制台中端口是否正确映射\n")
    
    # 启动 Gradio 服务器
    demo.launch(
        server_name="0.0.0.0",  # 允许所有IP访问
        server_port=7860,       # 使用7860端口
        share=False,            # 禁用不稳定的分享功能
        auth=None,              # 不需要认证
        show_error=True,        # 显示详细错误信息
        quiet=False             # 显示完整日志
    )