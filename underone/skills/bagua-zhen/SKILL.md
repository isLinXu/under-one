---
metadata:
  name: "bagua-zhen"
  version: "10.0"
  author: "under-one"
  description: "八卦阵 - 生态协调中枢 - 中央监控与互斥仲裁"
  language: "zh"
  tags: ['ecosystem', 'coordinator', 'dashboard', 'monitoring', 'metrics']
  icon: "☯"
  color: "#f0883e"
---

# ☯ 八卦阵 (Bagua-Zhen)

> **生态协调中枢 - 中央监控与互斥仲裁**

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

- 生态监控
- 效能聚合
- 互斥检测
- 协同增益
- 十技全景
- 监控面板

## 功能概述

八奇技skill生态系统的中央协调器：扫描所有skill状态、互斥检测与仲裁、效能聚合评分、生成生态健康报告和HTML监控面板

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/coordinator.py`

## 输入输出

### 输入

运行时数据目录 runtime_data/*_metrics.jsonl：

```json
runtime_data/qiti-yuanliu_metrics.jsonl
```

### 输出

JSON生态报告 + HTML面板：

```json
{"ecosystem_level": "阵法大成", "average_quality": 88.5}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| ecosystem_level | 生态等级 | 阵法大成/稳固/松动/破损 |
| average_quality | 平均质量 | 0-100 |
| active_skills | 活跃skill数 | 0-10 |
| mutex_pairs | 互斥对 | [] |

## API接口

| 接口 | 说明 |
|------|------|
| `coordinate(skills_dir)` | 执行生态协调 |
| `load_metrics(skill_name)` | 加载skill指标 |
| `calc_stats(records)` | 计算统计数据 |

## 使用示例

### 命令行

```bash
python scripts/coordinator.py [skills_dir]
```

### Python API

```python
from scripts.coordinator import *

# TODO: 添加具体使用示例
```

## 可配置项

以下配置项支持从 `under-one.yaml` 外部化：

- `mutex_pairs`
- `synergy_pairs`

详见 [`_skill_config.py`](../../_skill_config.py) 配置加载器。

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "bagua_zhen"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
