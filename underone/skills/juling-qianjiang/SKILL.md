---
metadata:
  name: "juling-qianjiang"
  version: "9.0"
  author: "under-one"
  description: "拘灵遣将 - 多工具调度器 - 灵体调度与降级保护"
  language: "zh"
  tags: ['dispatch', 'tool-orchestration', 'fallback', 'resilience']
  icon: "🐺"
  color: "#a5d6ff"
---

# 🐺 拘灵遣将 (Juling-Qianjiang)

> **多工具调度器 - 灵体调度与降级保护**

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

- 工具调度
- 多工具协调
- 降级保护
- 服灵模式
- 百鬼夜行
- 工具编排

## 功能概述

多工具调度与健康监控，工具不可用时执行降级保护（跳过/模拟/缓存），可选服灵模式内化生成替代实现

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/dispatcher.py`

## 输入输出

### 输入

JSON任务列表 + 工具列表：

```json
tasks.json + spirits.json
```

### 输出

JSON调度报告：

```json
{"plan": [...], "fallback_count": 0, "avg_quality": 95.0}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| fallback_count | 降级次数 | 0+ |
| avg_quality | 平均质量 | 0-100% |
| all_success | 全部成功 | true/false |

## API接口

| 接口 | 说明 |
|------|------|
| `dispatch(tasks, spirits, strategy)` | 执行调度 |
| `match_spirit(task, spirits)` | 匹配最适合的工具 |
| `fallback_protect(spirit)` | 降级保护 |
| `fallback_possess(spirit)` | 强制服灵 |

## 使用示例

### 命令行

```bash
python scripts/dispatcher.py tasks.json spirits.json protect
```

### Python API

```python
from scripts.dispatcher import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "juling_qianjiang"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
