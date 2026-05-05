---
metadata:
  name: "liuku-xianzei"
  version: "5.0"
  author: "under-one"
  description: "六库仙贼 - 知识消化器（信息保鲜）"
  language: "zh"
  tags: ["knowledge", "digest", "freshness", "information-quality"]
  icon: "🍃"
  color: "#ffdcd7"
---

# 六库仙贼 (LiuKu-XianZei)

## 触发词
- 知识消化
- 信息保鲜
- 消化率评估
- 知识质量
- 反刍调度

## 用途
评估信息消化率，生成知识单元，计算保鲜期，输出反刍（复习）调度计划。

## 输入
JSON信息列表：
```json
[
  {
    "source": "博客",
    "content": "Python 3.12 新特性...",
    "credibility": "A",
    "category": "技术方案"
  }
]
```

## 输出
JSON消化报告：
```json
{
  "avg_digestion_rate": 78.5,
  "distribution": {"高": 3, "中": 2, "低": 1},
  "knowledge_units": [
    {
      "concept": "Python 3.12新特性...",
      "digestion_rate": 85.0,
      "digestion_level": "高",
      "freshness_days": 90,
      "expires": "2026-08-01"
    }
  ],
  "review_schedule": [
    {"concept": "...", "review_in": "4小时", "reason": "低消化率"}
  ]
}
```

## 可信度权重
| 等级 | 权重 |
|------|------|
| S | 1.5x |
| A | 1.2x |
| B | 1.0x |
| C | 0.6x |

## 保鲜期规则
| 类别 | 保鲜期 |
|------|--------|
| 技术方案 | 90天 |
| 行业数据 | 180天 |
| 基础理论 | 3年 |
| 法律法规 | 7天 |
| 社区经验 | 90天 |

## 用法
```bash
python scripts/knowledge_digest.py <info.json>
```

## 依赖
- Python 3.8+
- 无外部依赖
