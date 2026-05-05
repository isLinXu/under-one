---
metadata:
  name: "bagua-zhen"
  version: "10.0"
  author: "under-one"
  description: "八卦阵 - 生态协调中枢（中央监控）"
  language: "zh"
  tags: ["ecosystem", "coordinator", "dashboard", "monitoring", "metrics"]
  icon: "☯"
  color: "#f0883e"
---

# 八卦阵 (Bagua-Zhen)

## 触发词
- 生态监控
- 效能聚合
- 互斥检测
- 协同增益
- 十技全景
- 监控面板

## 用途
八奇技skill生态系统的中央协调器：扫描所有skill状态、互斥检测与仲裁、效能聚合评分、生成生态健康报告和HTML监控面板。

## 输入
运行时数据目录 `runtime_data/*_metrics.jsonl`

## 输出
JSON生态报告 + HTML监控面板：
```json
{
  "ecosystem_level": "阵法大成",
  "average_quality": 88.5,
  "active_skills": 8,
  "mutex_pairs": [],
  "synergy_pairs": [["tongtian-lu", "dalu-dongguan"]],
  "skill_states": {...}
}
```

## 互斥矩阵
| Skill A | Skill B | 原因 |
|---------|---------|------|
| tongtian-lu | shenji-bailian | 瞬发 vs 锻造冲突 |
| qiti-yuanliu | fenghou-qimen | 扫描 vs 排盘干扰 |
| dalu-dongguan | liuku-xianzei | 洞察 vs 消化资源竞争 |

## 协同矩阵
| Skill A | Skill B | 增益 |
|---------|---------|------|
| tongtian-lu | dalu-dongguan | 符箓+洞察增强 |
| juling-qianjiang | shenji-bailian | 调度+锻造高效 |
| qiti-yuanliu | shuangquanshou | 扫描+守护稳定 |

## 用法
```bash
python scripts/coordinator.py [skills_dir]
python scripts/dashboard.py
```

## 依赖
- Python 3.8+
- 无外部依赖
