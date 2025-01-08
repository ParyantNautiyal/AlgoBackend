from setuptools import setup, find_packages

setup(
    name="trading-app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-dotenv>=0.19.0",
        "kiteconnect>=4.2.0",
        "mysqlclient>=2.0.3",
        "pytest>=7.0.0",
    ],
) 