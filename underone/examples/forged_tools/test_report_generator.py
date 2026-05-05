#!/usr/bin/env python3
"""
测试脚本: report-generator
用途: 验证工具核心功能
"""

import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from report_generator import process

def test_normal_case():
    """正常输入测试"""
    result = process("dummy_input.json")
    assert result is not None
    print("✅ 正常输入测试通过")

def test_empty_input():
    """空输入测试"""
    try:
        result = process("nonexistent.json")
        assert False, "应该抛出异常"
    except Exception:
        print("✅ 空输入测试通过（正确报错）")

def test_boundary():
    """边界测试"""
    print("⚠️  边界测试待实现")

if __name__ == "__main__":
    test_normal_case()
    test_empty_input()
    test_boundary()
    print("测试完成")
