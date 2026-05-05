---
metadata:
  name: "fenghou-qimen"
  version: "5.0"
  author: "under-one"
  description: "风后奇门 - 优先级引擎 - 任务排盘与调度"
  language: "zh"
  tags: ['priority', 'scheduling', 'task-ranking', 'monte-carlo']
  icon: "🧭"
  color: "#ff7b72"
---

# 🧭 风后奇门 (FengHou-QiMen)

> **优先级引擎 - 任务排盘与调度**

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

- 任务优先级
- 任务排序
- 八门排盘
- 优先级评分
- 执行计划
- 蒙特卡洛

## 功能概述

对多个任务进行九维度综合评分，映射到八门（开门/生门/景门/杜门/死门），通过蒙特卡洛模拟评估鲁棒性，输出执行计划

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/priority_engine.py`

## 输入输出

### 输入

JSON任务列表：

```json
[{"name": "任务A", "urgency": 5, "importance": 5}]
```

### 输出

JSON排盘报告：

```json
{"ranked_tasks": [...], "execution_plan": [...], "monte_carlo": {...}}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| composite_score | 综合评分 | 0-5 |
| gate | 八门映射 | 开门/生门/景门/杜门/死门 |
| on_time_rate | 按时完成率 | 蒙特卡洛模拟 |

## API接口

| 接口 | 说明 |
|------|------|
| `PriorityEngine(tasks)` | 创建引擎实例 |
| `.run()` | 执行评分和排盘 |
| `._score_all()` | 九维度评分 |
| `._assign_gates()` | 八门映射 |
| `._monte_carlo()` | 鲁棒性模拟 |

## 使用示例

### 命令行

```bash
python scripts/priority_engine.py <tasks.json>
```

### Python API

```python
from scripts.priority_engine import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "fenghou_qimen"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
