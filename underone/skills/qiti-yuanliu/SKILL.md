---
metadata:
  name: "qiti-yuanliu"
  version: "5.0"
  author: "under-one"
  description: "炁体源流 - 上下文稳态扫描器 - 检测对话健康状态"
  language: "zh"
  tags: ['context', 'entropy', 'health-check', 'monitoring']
  icon: "🔍"
  color: "#7ee787"
---

# 🔍 炁体源流 (QiTi-YuanLiu)

> **上下文稳态扫描器 - 检测对话健康状态**

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

- 上下文健康检查
- 扫描对话状态
- 检测上下文漂移
- 计算上下文熵
- 对话质量评估

## 功能概述

扫描Agent对话上下文，计算健康指标（熵、一致性、对齐度、完整度），输出诊断报告和修复建议

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/entropy_scanner.py`

## 输入输出

### 输入

JSON格式的对话上下文：

```json
[{"role": "user", "content": "...", "round": 1}]
```

### 输出

JSON诊断报告：

```json
{"entropy": 2.5, "consistency": 85, "health_score": 82.5}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| entropy | 上下文熵（矛盾+缺口+冗余） | warning: 3.0, critical: 7.0 |
| consistency | 一致性 | min: 60% |
| alignment | 目标对齐度 | - |
| completeness | 推理链完整度 | - |
| health_score | 综合健康分 | excellent: 90+, good: 75+ |

## API接口

| 接口 | 说明 |
|------|------|
| `QiTiScanner(context_data)` | 创建扫描器实例 |
| `.scan()` | 执行全量扫描，返回诊断报告 |
| `._calc_entropy()` | 计算上下文熵 |
| `._check_consistency()` | 检查上下文一致性 |
| `._calc_health_score()` | 计算综合健康分 |

## 使用示例

### 命令行

```bash
python scripts/entropy_scanner.py <context.json>
```

### Python API

```python
from scripts.entropy_scanner import *

# TODO: 添加具体使用示例
```

## 可配置项

以下配置项支持从 `under-one.yaml` 外部化：

- `entropy_warning`
- `entropy_critical`
- `consistency_min`

详见 [`_skill_config.py`](../../_skill_config.py) 配置加载器。

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "qiti_yuanliu"
```

## 依赖环境

- Python 3.8+
- 无外部依赖（纯标准库）

---

*Generated for under-one.skills framework*
