#!/usr/bin/env python
"""
家庭版智能照片系统 - 包安装配置
"""

from setuptools import setup, find_packages
import os

# 读取requirements.txt
def read_requirements():
    """读取requirements.txt文件"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# 项目描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="photos-system",
    version="1.0.0",
    author="AI助手",
    author_email="ai@example.com",
    description="家庭版智能照片系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/photos-system",

    # 包发现
    packages=find_packages(exclude=['tests', 'tests.*', 'abandon', 'abandon.*', '1.prepare']),

    # 包数据
    package_data={
        'app': ['*.py'],
    },

    # Python版本要求
    python_requires='>=3.8',

    # 依赖包
    install_requires=read_requirements(),

    # 额外依赖
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
            'pre-commit>=2.17.0',
        ],
        'docs': [
            'sphinx>=4.5.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
    },

    # 控制台脚本
    entry_points={
        'console_scripts': [
            'photos-system=main:main',
        ],
    },

    # 分类器
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Utilities',
    ],

    # 关键词
    keywords='photo management ai analysis organization',

    # 项目状态
    zip_safe=False,
)
