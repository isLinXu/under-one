---
metadata:
  name: "liuku-xianzei"
  version: "5.0"
  author: "under-one"
  description: "六库仙贼 - 知识消化器 - 信息保鲜与质量评估"
  language: "zh"
  tags: ['knowledge', 'digest', 'freshness', 'information-quality']
  icon: "🍃"
  color: "#ffdcd7"
---

# 🍃 六库仙贼 (LiuKu-XianZei)

> **知识消化器 - 信息保鲜与质量评估**

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

- 知识消化
- 信息保鲜
- 消化率评估
- 知识质量
- 反刍调度

## 功能概述

评估信息消化率，生成知识单元，计算保鲜期，输出反刍（复习）调度计划

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/knowledge_digest.py`

## 输入输出

### 输入

JSON信息列表：

```json
[{"source": "博客", "content": "...", "credibility": "A", "category": "技术方案"}]
```

### 输出

JSON消化报告：

```json
{"avg_digestion_rate": 78.5, "knowledge_units": [...], "review_schedule": [...]}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| digestion_rate | 消化率 | 0-100% |
| freshness_days | 保鲜期 | 7-1095天 |
| credibility_weight | 可信度权重 | S:1.5, A:1.2, B:1.0, C:0.6 |

## API接口

| 接口 | 说明 |
|------|------|
| `KnowledgeDigest(items)` | 创建消化器实例 |
| `.digest()` | 执行知识消化 |
| `._process(item)` | 处理单个信息项 |

## 使用示例

### 命令行

```bash
python scripts/knowledge_digest.py <info.json>
```

### Python API

```python
from scripts.knowledge_digest import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "liuku_xianzei"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
