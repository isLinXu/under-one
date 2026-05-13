---
metadata:
  name: "tongtian-lu"
  version: "v0.1.0"
  author: "under-one"
  description: "通天箓 - 符箓生成器 - 结构化任务拆解、模式化符阵编排与执行拓扑生成"
  language: "zh"
  tags: ['command', 'template', 'task-planning', 'talisman', 'topology', 'conflict-detection', 'structured-spec', 'orchestration-mode']
  icon: "📜"
  color: "#79c0ff"
---

# 通天箓 (TongTian-Lu)

> 符箓生成器 - 将任务意图拆为符箓序列、风险预算与执行拓扑。

## 触发词

- 生成符箓
- 任务拆解
- 执行计划
- 拓扑编排
- 风险检测
- 结构化任务规格
- 符阵编排

## 功能概述

`通天箓` 会根据任务描述或结构化任务规格，生成一组适合的符箓（分析/创作/验证/转换/检索/决策），并输出冲突、禁咒等级、执行拓扑与执行模式。

V5.8 的升级重点：

1. **结构化输入**：支持 `task / talisman_contract / risk_contract / execution_contract`
2. **模式化编排**：支持 `quick-cast / balanced-array / full-ritual`
3. **语义化输出**：新增 `orchestration_mode / ritual_intent / ritual_summary / risk_alignment`
4. **向后兼容**：原有“直接传任务字符串”的用法保持可用

```mermaid
graph LR
    A[任务描述 / JSON spec] --> B[关键词与契约解析]
    B --> C[符箓筛选]
    C --> D[风险与冲突检测]
    D --> E[执行拓扑生成]
    E --> F[计划与摘要输出]
```

## 输入输出

- 输入清单：`任务描述字符串`、`task.txt`、`task_spec.json`
- 输出清单：`fu_plan.json`

### 1. 旧版字符串输入

```bash
python scripts/fu_generator.py '搜索资料并生成报告'
```

### 2. 结构化 JSON 规格

```json
{
  "task": {
    "description": "搜索资料并分析后生成报告"
  },
  "talisman_contract": {
    "preferred_types": ["retrieval", "analysis"],
    "blocked_types": ["transformation"]
  },
  "risk_contract": {
    "max_curse_level": "medium"
  },
  "execution_contract": {
    "orchestration_mode": "balanced-array",
    "sla_target": 60
  }
}
```

## 编排模式

| 模式 | 说明 | 典型行为 |
|------|------|----------|
| `quick-cast` | 快速拆解 | 压缩到少量核心符箓，优先快速成阵 |
| `balanced-array` | 平衡编排 | 默认模式，兼顾覆盖率和复杂度 |
| `full-ritual` | 完整仪式 | 保留更多符箓，并自动补验证尾阵 |

说明：
- 默认模式是 `balanced-array`
- `full-ritual` 适合高要求、多阶段任务
- `quick-cast` 适合先拉起一版执行骨架

## 工作流程

1. 解析任务字符串或结构化 spec
2. 基于关键词匹配基础符箓
3. 应用契约偏好：补入 `preferred_types`，移除 `blocked_types`
4. 依据编排模式裁剪或增强符阵
5. 检测禁咒、风险越界、数据流和约束冲突
6. 构建拓扑，输出执行计划和语义化摘要

## 输出结构

V5.8 返回结果示例（可落盘为 `fu_plan.json`）：

```json
{
  "generator": "tongtian-lu",
  "version": "v0.1.0",
  "task": "搜索资料并分析后生成报告",
  "orchestration_mode": "balanced-array",
  "ritual_intent": "balanced orchestration",
  "dimension_count": 3,
  "curse_level": "low",
  "risk_alignment": "within_budget",
  "topology": ["retrieval-v5.0", "analysis-v5.0", "creation-v5.0"],
  "ritual_summary": {
    "orchestration_mode": "balanced-array",
    "ritual_intent": "balanced orchestration",
    "topology_strategy": "balanced-lattice",
    "preferred_talismans": ["retrieval", "analysis"],
    "blocked_talismans": ["transformation"],
    "risk_budget": "medium",
    "risk_alignment": "within_budget",
    "sla_target": 60,
    "contracts_present": [
      "task",
      "talisman_contract",
      "risk_contract",
      "execution_contract"
    ],
    "parallelizable_groups": 2
  },
  "execution_plan": {
    "mode": "parallel_where_possible",
    "estimated_sla": 45,
    "adapter_insertions": 0
  }
}
```

## 配置说明

配置路径：`under-one.yaml > tongtianlu`

除原有关键词、禁咒、SLA 和顺序配置外，V5.8 新增：

```yaml
tongtianlu:
  orchestration_modes:
    modes:
      quick-cast:
        max_talismans: 2
        include_verification_tail: false
        prefer_parallel: true
        topology_strategy: "minimal-chain"
        intent: "rapid decomposition"
      balanced-array:
        max_talismans: 4
        include_verification_tail: false
        prefer_parallel: true
        topology_strategy: "balanced-lattice"
        intent: "balanced orchestration"
      full-ritual:
        max_talismans: 6
        include_verification_tail: true
        prefer_parallel: false
        topology_strategy: "full-stack ritual"
        intent: "full-stack execution lattice"
```

## API接口

| 接口 | 签名 | 说明 |
|------|------|------|
| CLI | `python scripts/fu_generator.py <task_or_spec>` | 生成符箓执行计划 |
| Python | `FuGenerator(spec).generate() -> dict` | 返回拓扑、风险和仪式摘要 |

## 使用示例

### 命令行

```bash
python scripts/fu_generator.py task.txt
python scripts/fu_generator.py task_spec.json
```

### Python API

```python
from scripts.fu_generator import FuGenerator

spec = {
    "task": {"description": "搜索资料并分析后生成报告"},
    "talisman_contract": {"preferred_types": ["retrieval", "analysis"]},
    "execution_contract": {"orchestration_mode": "full-ritual"},
}

gen = FuGenerator(spec)
result = gen.generate()

print(result["orchestration_mode"])
print(result["ritual_summary"])
print(result["topology"])
```

## 测试方法

当前已覆盖：

- 旧版字符串输入兼容性
- 结构化任务规格支持
- `quick-cast` 模式压缩符箓数量
- `blocked_types` 对结果的筛除效果

建议回归命令：

```bash
pytest underone/tests/test_skills_core.py -q
pytest underone/tests/test_skills_core.py underone/tests/test_under_one.py
```

## 版本变更

### V5.8

- 支持结构化任务规格
- 引入编排模式控制符阵强度
- 输出仪式意图、风险对齐与编排摘要
- 保持旧版字符串任务输入兼容

### V5.2

- 从配置加载关键词、禁咒、SLA 与拓扑顺序
