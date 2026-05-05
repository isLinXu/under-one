#!/usr/bin/env python3
"""
under-one.skills — 八奇技Agent运维框架
pip installable setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="under-one-skills",
    version="10.0.0",
    author="under-one.skills Team",
    description="八奇技Agent运维框架 — 10个独立skill解决LLM Agent工程问题",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/isLinXu/under-one",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        # 核心依赖（尽量保持轻量）
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov", "black", "flake8"],
        "viz": ["matplotlib>=3.5", "numpy>=1.21"],
        "openai": ["openai>=1.0"],
        "anthropic": ["anthropic>=0.34"],
        "llm": ["openai>=1.0", "anthropic>=0.34"],
    },
    entry_points={
        "console_scripts": [
            "under-one=under_one.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "under_one": ["under-one.yaml"],
    },
    zip_safe=False,
)
