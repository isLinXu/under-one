---
metadata:
  name: "tongtian-lu"
  version: "5.0"
  author: "under-one"
  description: "通天箓 - 符箓生成器 - 任务拆解与执行计划"
  language: "zh"
  tags: ['command', 'template', 'task-planning', 'talisman']
  icon: "📜"
  color: "#79c0ff"
---

# 📜 通天箓 (TongTian-Lu)

> **符箓生成器 - 任务拆解与执行计划**

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

- 生成符箓
- 任务拆解
- 指令模板
- 执行计划
- 符箓冲突检测

## 功能概述

根据自然语言任务描述，自动生成符箓模板（分析箓、创作箓、验证箓等），检测符箓间冲突，输出执行拓扑和预估耗时

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/fu_generator.py`

## 输入输出

### 输入

任务描述字符串或文本文件：

```json
'分析竞品数据并生成报告' 或 task.txt
```

### 输出

JSON执行计划：

```json
{"talisman_list": [...], "topology": [...], "execution_plan": {...}}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| dimension_count | 检测到的维度数 | - |
| curse_level | 禁咒等级（高危/中危/低危） | - |
| conflicts | 符箓间冲突数 | 0+ |
| estimated_sla | 预估总耗时 | 秒 |

## API接口

| 接口 | 说明 |
|------|------|
| `FuGenerator(task_desc)` | 创建生成器实例 |
| `.generate()` | 生成符箓计划和拓扑 |
| `._detect_dimensions()` | 检测任务维度 |
| `._detect_conflicts()` | 检测符箓冲突 |
| `._build_topology()` | 构建执行拓扑 |

## 使用示例

### 命令行

```bash
python scripts/fu_generator.py '<任务描述>'
```

### Python API

```python
from scripts.fu_generator import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "tongtian_lu"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
