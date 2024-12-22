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
        "faiss-cpu",
        "numpy",
        "pandas",
        "chromadb",
        "langchain-community>=0.0.10",
        "langchain-core>=0.1.0",
        "langchain>=0.1.0"
    ]
) 