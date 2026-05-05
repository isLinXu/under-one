---
metadata:
  name: "shuangquanshou"
  version: "5.0"
  author: "under-one"
  description: "双全手 - DNA校验器（人格守护）"
  language: "zh"
  tags: ["persona", "dna", "validation", "style-guard", "drift-detection"]
  icon: "✋"
  color: "#aff5b4"
---

# 双全手 (ShuangQuanShou)

## 触发词
- DNA校验
- 人格守护
- 风格漂移
- 人设检查
- 风格切换验证

## 用途
计算风格偏离度，检测人格漂移，校验DNA一致性，防止核心人设被违背。

## 输入
JSON人格档案：
```json
{
  "current_style": {"tone": 3, "formality": 4, "detail_level": 3, "structure": 4},
  "dna_expectation": {"tone": 3, "formality": 4, "detail_level": 3, "structure": 4},
  "dna_core": {"诚信": "不编造", "安全": "不医疗法律投资"},
  "requested_change": {"type": "tone", "target": "更随意"},
  "history": [{"style": "formal"}, {"style": "formal"}]
}
```

## 输出
JSON校验报告：
```json
{
  "deviation_score": 0.15,
  "drift_level": "green",
  "dna_violations": [],
  "can_switch": true,
  "recommendations": ["DNA一致，允许风格调整"]
}
```

## 校验维度
| 维度 | 说明 |
|------|------|
| tone | 语气语调 |
| formality | 正式程度 |
| detail_level | 详细程度 |
| structure | 结构偏好 |

## 漂移等级
| 偏离度 | 等级 | 建议 |
|--------|------|------|
| <0.2 | green | 正常 |
| 0.2-0.4 | yellow | 轻微漂移，关注 |
| >0.4 | red | 严重漂移，立即校准 |

## 用法
```bash
python scripts/dna_validator.py <profile.json>
```

## 依赖
- Python 3.8+
- 无外部依赖
