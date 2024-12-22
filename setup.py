from setuptools import setup, find_packages

setup(
    name="medical_ai",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "torch",
        "transformers",
        "gradio",
        "sentence-transformers",
        "faiss-cpu",  # 或 faiss-gpu
        "numpy",
        "pandas"
    ]
) 