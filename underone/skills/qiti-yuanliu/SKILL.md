---
metadata:
  name: "qiti-yuanliu"
  version: "5.0"
  author: "under-one"
  description: "炁体源流 - 上下文稳态扫描器"
  language: "zh"
  tags: ["context", "entropy", "health-check", "monitoring"]
  icon: "🔍"
  color: "#7ee787"
---

# 炁体源流 (QiTi-YuanLiu)

## 触发词
- 上下文健康检查
- 扫描对话状态
- 检测上下文漂移
- 计算上下文熵
- 对话质量评估

## 用途
扫描Agent对话上下文，计算健康指标（熵、一致性、对齐度、完整度），输出诊断报告和修复建议。

## 输入
JSON格式的对话上下文：
```json
[
  {"role": "user", "content": "...", "round": 1},
  {"role": "assistant", "content": "...", "round": 1}
]
```

## 输出
JSON诊断报告：
```json
{
  "entropy": 2.5,
  "consistency": 85,
  "alignment": 90,
  "completeness": 75,
  "health_score": 82.5,
  "health_level": "good",
  "alerts": [],
  "recommendations": ["建议关注，执行轻量炁循环"]
}
```

## 核心指标
| 指标 | 说明 | 阈值 |
|------|------|------|
| entropy | 上下文熵（矛盾+缺口+冗余） | warning: 3.0, critical: 7.0 |
| consistency | 一致性 | min: 60% |
| alignment | 目标对齐度 | - |
| completeness | 推理链完整度 | - |
| health_score | 综合健康分 | excellent: 90+, good: 75+, warning: 60+ |

## 用法
```bash
python scripts/entropy_scanner.py <context.json>
```

## 依赖
- Python 3.8+
- 无外部依赖（纯标准库）
