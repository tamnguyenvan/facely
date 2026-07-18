"""Setup script for Facely."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Facely",
    version="1.0.0",
    author="Facely Contributors",
    description="Production-grade facial recognition desktop system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/Facely",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "onnxruntime>=1.17.0",
        "opencv-python>=4.9.0",
        "numpy>=1.26.0",
        "PySide6>=6.6.0",
        "scipy>=1.12.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "Facely=main:main",
        ],
    },
)
