---
metadata:
  name: "xiushen-lu"
  version: "7.0"
  author: "under-one"
  description: "修身炉 - 自进化中枢 - Agent进化引擎"
  language: "zh"
  tags: ['evolution', 'self-improvement', 'adaptive', 'threshold', 'learning']
  icon: "🔥"
  color: "#f778ba"
---

# 🔥 修身炉 (XiuShen-Lu)

> **自进化中枢 - Agent进化引擎**

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

- 技能进化
- 自进化
- 阈值自适应
- 深度进化
- 跨技能学习
- 知识迁移

## 功能概述

Agent自进化中枢V7：自适应阈值引擎（根据历史数据动态调整）、深度进化（优化脚本内部参数）、跨skill学习（借鉴其他skill优化经验）、知识迁移（验证有效的阈值自动共享）

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/core_engine.py`

## 输入输出

### 输入

运行时指标数据 runtime_data/*_metrics.jsonl：

```json
runtime_data/qiti-yuanliu_metrics.jsonl
```

### 输出

JSON进化报告：

```json
{"results": [...], "summary": {"evolved": 2, "failed_rolled_back": 0}}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| evolution_type | 进化类型 | tuning/extension/refactor/none |
| health_score | 健康分 | 0-100 |
| bottleneck_type | 瓶颈类型 | stable/error_prone/low_autonomy/unstable |

## API接口

| 接口 | 说明 |
|------|------|
| `XiuShenLuCoreV7(skills_dir)` | 创建进化引擎 |
| `.run_evolution_cycle(skill_name)` | 执行进化周期 |
| `QiSourceV7.collect(metric)` | 收集运行时指标 |
| `RefinerV7.analyze(skill_name, records)` | 分析skill状态 |
| `TransformerV7.evolve(skill_name, type, analysis)` | 执行进化 |

## 使用示例

### 命令行

```bash
python scripts/core_engine.py <skills_dir> [skill_name]
```

### Python API

```python
from scripts.core_engine import *

# TODO: 添加具体使用示例
```

## 可配置项

以下配置项支持从 `under-one.yaml` 外部化：

- `success_rate_warning`
- `success_rate_critical`
- `human_intervention_warning`

详见 [`_skill_config.py`](../../_skill_config.py) 配置加载器。

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "xiushen_lu"
```

## 依赖环境

- Python 3.8+
- 可选: shared_knowledge.py

---

*Generated for under-one.skills framework*
