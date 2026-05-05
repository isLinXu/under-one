---
metadata:
  name: "shenji-bailian"
  version: "5.0"
  author: "under-one"
  description: "神机百炼 - 工具工厂 - 代码生成与脚手架"
  language: "zh"
  tags: ['code-generation', 'tool-factory', 'scaffolding', 'template']
  icon: "🔨"
  color: "#ffa657"
---

# 🔨 神机百炼 (ShenJi-BaiLian)

> **工具工厂 - 代码生成与脚手架**

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

- 生成工具
- 代码脚手架
- 工具模板
- 锻造工具
- 生成脚本框架

## 功能概述

根据需求描述自动生成可执行的Python脚本框架、测试脚本和契约文档

## 架构设计

```
输入 → 解析 → 核心处理 → 指标计算 → 报告生成 → 输出
```

入口文件: `scripts/tool_factory.py`

## 输入输出

### 输入

JSON规格说明：

```json
{"name": "json_cleaner", "description": "清洗JSON", "inputs": ["raw.json"]}
```

### 输出

工具代码+测试+契约：

```json
{"tool_code": "...", "test_code": "...", "contract": "..."}
```

## 核心指标

| 指标 | 说明 | 阈值/范围 |
|------|------|-----------|
| files_generated | 生成文件数 | 3 |
| template_coverage | 模板覆盖率 | 100% |

## API接口

| 接口 | 说明 |
|------|------|
| `ToolFactory(spec)` | 创建工厂实例 |
| `.forge()` | 生成工具代码和测试 |

## 使用示例

### 命令行

```bash
python scripts/tool_factory.py <spec.json>
```

### Python API

```python
from scripts.tool_factory import *

# TODO: 添加具体使用示例
```

## 测试方法

```bash
# 运行相关测试
python -m pytest underone/tests/test_skills_core.py -v -k "shenji_bailian"
```

## 依赖环境

- Python 3.8+
- 无外部依赖

---

*Generated for under-one.skills framework*
