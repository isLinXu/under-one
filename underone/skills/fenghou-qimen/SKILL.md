---
metadata:
  name: "fenghou-qimen"
  version: "5.0"
  author: "under-one"
  description: "风后奇门 - 优先级引擎（任务排盘）"
  language: "zh"
  tags: ["priority", "scheduling", "task-ranking", "monte-carlo"]
  icon: "🧭"
  color: "#ff7b72"
---

# 风后奇门 (FengHou-QiMen)

## 触发词
- 任务优先级
- 任务排序
- 八门排盘
- 优先级评分
- 执行计划
- 蒙特卡洛

## 用途
对多个任务进行九维度综合评分，映射到八门（开门/生门/景门/杜门/死门），通过蒙特卡洛模拟评估鲁棒性，输出执行计划。

## 输入
JSON任务列表：
```json
[
  {
    "name": "任务A",
    "urgency": 5,
    "importance": 5,
    "dependency": 3,
    "deadline_pressure": 4,
    "estimated_time": 30
  }
]
```

## 输出
JSON排盘报告：
```json
{
  "ranked_tasks": [...],
  "execution_plan": [
    {"task": "任务A", "score": 4.2, "gate": "生门", "action": "重点推进"}
  ],
  "monte_carlo": {"simulations": 100, "on_time_rate": 85.3}
}
```

## 八门映射
| 得分范围 | 八门 | 行动建议 |
|----------|------|----------|
| 4.5+ | 开门 | 立即启动 |
| 4.0-4.5 | 生门 | 重点推进 |
| 3.2-4.0 | 景门 | 审视后执行 |
| 2.5-3.2 | 杜门 | 绕过障碍/延后 |
| <2.5 | 死门 | 终止释放资源 |

## 评分维度
紧急度(25%) + 重要性(35%) + 依赖度(15%) + 资源匹配(10%) + 时限压力(10%) + 环境就绪(5%) + 团队匹配(5%)

## 用法
```bash
python scripts/priority_engine.py <tasks.json>
```

## 依赖
- Python 3.8+
- 无外部依赖
