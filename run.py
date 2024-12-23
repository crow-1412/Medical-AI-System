import os
import asyncio
import torch
import gradio as gr
from interface.gradio_app import create_gradio_interface
from config.config import Config

def check_dependencies() -> bool:
    """检查必要的依赖是否满足"""
    try:
        # 检查必要的Python包
        import torch
        import gradio
        import transformers
        import jieba
        
        print("所有依赖项检查通过！")
        return True
        
    except ImportError as e:
        print(f"缺少必要的依赖项: {str(e)}")
        return False

def setup_environment():
    """设置运行环境"""
    print("正在设置运行环境...")
    
    # 检查CUDA是否可用
    if torch.cuda.is_available():
        n_gpus = torch.cuda.device_count()
        print(f"检测到 {n_gpus} 个 GPU 设备:")
        for i in range(n_gpus):
            gpu_name = torch.cuda.get_device_name(i)
            memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"  GPU {i}: {gpu_name}")
            print(f"  显存: {memory:.1f}GB")
    else:
        print("未检测到 GPU 设备，将使用 CPU 运行")
    
    print("环境设置完成！\n")

async def main():
    """主函数"""
    # 1. 检查依赖
    if not check_dependencies():
        return
        
    # 2. 设置环境
    setup_environment()
    
    # 3. 创建必要的目录
    os.makedirs("/root/autodl-tmp/medical_ai_system", exist_ok=True)
    
    # 4. 创建Gradio界面
    print("正在启动 Web 界面...")
    demo = await create_gradio_interface()
    
    # 5. 启动服务
    print("\n系统启动完成！")
    print("访问说明:")
    print("1. 本地访问: http://localhost:7860")
    print("2. 远程访问:")
    print("   - 在 AutoDL 控制台中找到'开放端口'")
    print("   - 将端口 7860 映射到公网")
    print("   - 使用 AutoDL 提供的访问地址\n")
    
    demo.launch(
        server_name="0.0.0.0",
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    asyncio.run(main()) 