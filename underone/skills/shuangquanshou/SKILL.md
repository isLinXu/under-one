---
metadata:
  name: "shuangquanshou"
  version: "5.0"
  author: "under-one"
  description: "双全手 - DNA校验器 - 人格守护与漂移检测"
  language: "zh"
  tags: ['persona', 'dna', 'validation', 'style-guard', 'drift-detection']
  icon: "✋"
  color: "#aff5b4"
---

# ✋ 双全手 (ShuangQuanShou)

> **DNA校验器 - 人格守护与漂移检测**

## 目录

- [触发词](#触发词)
- [功能概述](#功能概述)
- [架构设计](#架构设计)
- [输入输出](#输入输出)
- [核心指标](#核心指标)
- [API接口](#api接口)
- [使用示例](#使用示例)
- [配置说明](#配置说明)
- [测试方法](#测试方法)
- [依赖环境](#依赖环境)

## 触发词

- DNA校验
- 人格守护
- 风格漂移
- 人设检查
- 风格切换验证

## 功能概述

计算风格偏离度，检测人格漂移，校验DNA一致性，防止核心人设被违背

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/dna_validator.py`

## 输入输出

### 输入

JSON人格档案：

```json
{"current_style": {"tone": 3}, "dna_expectation": {"tone": 3}}
```

### 输出

JSON校验报告：

```json
{"deviation_score": 0.15, "drift_level": "green", "can_switch": true}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| deviation_score | 偏离度 | 0-1 |
| drift_level | 漂移等级 | green/yellow/red |
| can_switch | 允许切换 | true/false |

## API接口

| 接口 | 说明 |
|------|------|
| `DNAValidator(profile)` | 创建校验器实例 |
| `.validate()` | 执行DNA校验 |
| `._calc_deviation()` | 计算偏离度 |
| `._check_dna_violations()` | 检查DNA违背 |

## 使用示例

### 命令行

```bash
python scripts/dna_validator.py <profile.json>
```

### Python API

```python
from scripts.dna_validator import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "shuangquanshou"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
