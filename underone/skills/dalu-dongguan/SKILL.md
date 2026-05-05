---
metadata:
  name: "dalu-dongguan"
  version: "5.0"
  author: "under-one"
  description: "大罗洞观 - 关联检测器 - 全局洞察与知识图谱"
  language: "zh"
  tags: ['link-detection', 'knowledge-graph', 'entity-extraction', 'insight']
  icon: "🔭"
  color: "#d2a8ff"
---

# 🔭 大罗洞观 (DaLu-DongGuan)

> **关联检测器 - 全局洞察与知识图谱**

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

- 检测关联
- 知识图谱
- 实体提取
- 关联分析
- 文本关联
- Mermaid图谱

## 功能概述

从多段文本中检测语义关联、共现实体、时序关系和因果关系，输出关联图谱和Mermaid可视化代码

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/link_detector.py`

## 输入输出

### 输入

JSON段落列表：

```json
[{"source": "A段", "content": "文本内容..."}]
```

### 输出

JSON关联报告：

```json
{"links": [...], "entity_map": {...}, "mermaid_code": "..."}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| entity_count | 提取实体数 | - |
| link_count | 关联数 | - |
| semantic_links | 语义关联 | Jaccard > 0.3 |
| cooccurrence_links | 共现实体关联 | - |

## API接口

| 接口 | 说明 |
|------|------|
| `LinkDetector(segments)` | 创建检测器实例 |
| `.detect()` | 执行关联检测 |
| `._extract_entities()` | 提取实体 |
| `._semantic_links()` | 语义相似度关联 |
| `._generate_mermaid()` | 生成Mermaid图表代码 |

## 使用示例

### 命令行

```bash
python scripts/link_detector.py <segments.json>
```

### Python API

```python
from scripts.link_detector import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "dalu_dongguan"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
