---
metadata:
  name: "xiushen-lu"
  version: "7.0"
  author: "under-one"
  description: "修身炉 - 自进化中枢（Agent进化引擎）"
  language: "zh"
  tags: ["evolution", "self-improvement", "adaptive", "threshold", "learning"]
  icon: "🔥"
  color: "#f778ba"
---

# 修身炉 (XiuShen-Lu)

## 触发词
- 技能进化
- 自进化
- 阈值自适应
- 深度进化
- 跨技能学习
- 知识迁移

## 用途
Agent自进化中枢V7：自适应阈值引擎（根据历史数据动态调整）、深度进化（优化脚本内部参数）、跨skill学习（借鉴其他skill优化经验）、知识迁移（验证有效的阈值自动共享）。

## 输入
运行时指标数据 `runtime_data/*_metrics.jsonl`

## 输出
JSON进化报告：
```json
{
  "results": [
    {
      "skill": "qiti-yuanliu",
      "status": "evolved",
      "evolution": {
        "evolution_type": "tuning",
        "version": "v5.1.0",
        "changes": ["阈值放宽20%"],
        "deep_evolution": true
      }
    }
  ],
  "summary": {"total": 10, "evolved": 2, "failed_rolled_back": 0, "no_action": 8}
}
```

## 进化类型
| 类型 | 触发条件 | 操作 |
|------|----------|------|
| tuning | 轻微退化 | 参数微调 |
| extension | 功能不足 | 逻辑扩展 |
| refactor | 严重退化 | 架构重构 |

## 自适应阈值
- 成功率>95%且方差<5：放宽阈值
- 方差>15：收紧阈值
- 连续退化>=4次：触发进化

## 核心组件
| 组件 | 职责 |
|------|------|
| QiSourceV7 | 运行时数据收集 |
| RefinerV7 | 自适应阈值+瓶颈分析 |
| TransformerV7 | 深度进化+知识迁移 |
| RollbackV7 | 版本回退 |

## 用法
```bash
python scripts/core_engine.py <skills_dir> [skill_name]
```

## 依赖
- Python 3.8+
- 可选: shared_knowledge.py（跨skill知识共享）
