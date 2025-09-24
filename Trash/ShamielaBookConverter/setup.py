#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# قراءة وصف المشروع
def read_description():
    """قراءة وصف المشروع من README.md"""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "محول كتب الشاملة من Access إلى MySQL"

# قراءة المتطلبات
def read_requirements():
    """قراءة المتطلبات من requirements.txt"""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            requirements = []
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)
            return requirements
    except FileNotFoundError:
        return ["pyodbc>=4.0.35", "mysql-connector-python>=8.0.33", "pyinstaller>=5.13.0"]

setup(
    name="shamela-books-converter",
    version="2.0.0",
    author="GitHub Copilot AI Assistant",
    author_email="",
    description="محول كتب الشاملة من Access إلى MySQL",
    long_description=read_description(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: Arabic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "shamela-converter=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.ico", "*.png", "*.json"],
        "resources": ["*.*"],
        "resources/icons": ["*.ico", "*.png"],
        "resources/images": ["*.png", "*.jpg"],
        "resources/data": ["*.json", "*.sql"],
    },
    zip_safe=False,
    keywords="shamela books converter access mysql database arabic",
    project_urls={
        "Bug Reports": "",
        "Source": "",
        "Documentation": "",
    },
)