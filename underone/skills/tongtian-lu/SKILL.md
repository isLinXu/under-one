---
metadata:
  name: "tongtian-lu"
  version: "5.0"
  author: "under-one"
  description: "通天箓 - 符箓生成器（瞬发指令系统）"
  language: "zh"
  tags: ["command", "template", "task-planning", "talisman"]
  icon: "📜"
  color: "#79c0ff"
---

# 通天箓 (TongTian-Lu)

## 触发词
- 生成符箓
- 任务拆解
- 指令模板
- 执行计划
- 符箓冲突检测

## 用途
根据自然语言任务描述，自动生成符箓模板（分析箓、创作箓、验证箓等），检测符箓间冲突，输出执行拓扑和预估耗时。

## 输入
任务描述字符串或文本文件：
```bash
python scripts/fu_generator.py "分析竞品数据并生成报告"
```

## 输出
JSON执行计划：
```json
{
  "talisman_list": [...],
  "conflicts": [...],
  "topology": ["retrieval-v5.0", "analysis-v5.0", "creation-v5.0"],
  "execution_plan": {
    "mode": "serial",
    "estimated_sla": 45
  }
}
```

## 符箓类型
| 符箓 | 用途 | SLA |
|------|------|-----|
| 分析箓 | 信息解析与提取 | 10s |
| 创作箓 | 内容生成与改写 | 20s |
| 验证箓 | 逻辑检查与确认 | 15s |
| 转换箓 | 格式与结构变换 | 10s |
| 检索箓 | 信息查找与关联 | 15s |
| 决策箓 | 方案评估与选择 | 15s |

## 用法
```bash
python scripts/fu_generator.py '<任务描述>'
python scripts/fu_generator.py <task.txt>
```

## 依赖
- Python 3.8+
- 无外部依赖
