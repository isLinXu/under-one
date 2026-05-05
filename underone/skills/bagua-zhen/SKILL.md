---
name: bagua-zhen
description: 八卦阵——八奇技中央协调器，统一管理八技状态、互斥仲裁、效能聚合与全局调度。当八技中的多个技能同时激活或存在资源冲突时，八卦阵自动介入进行仲裁与调度。适用于八技协同、全局监控、冲突仲裁、效能总览场景。自动触发条件：检测到2个以上八技同时处于激活状态或用户请求"查看八技状态/效能报告"时自动启动。
---

## V7 Features

- Self-evolution via XiuShenLu engine
- Runtime metrics export to adaptive thresholds
- Cross-skill knowledge sharing
- Deep parameter optimization
- Linkage protocol for multi-skill orchestration


# 八卦阵

> 天、地、风、雷、水、火、山、泽，八卦相生相克，阵成则万法归一。

## 实战速查卡

| 触发条件 | 自动动作 | 目标产出 | 失败回退 |
|---------|---------|---------|---------|
| 2个以上八技同时激活 | 启动互斥仲裁 | 冲突消解方案 | 串行排队 |
| 用户请求"查看状态" | 生成效能总览 | 八技仪表盘 | 文字摘要 |
| 某技能效能连续低于60 | 发出全局警报 | 改进建议 | 静默记录 |
| 跨技能联动请求 | 路由到目标技能 | 协同执行链 | 单技能执行 |

## V5 中央协调器协议

### 状态总线

八卦阵维护八技实时状态表：

```
[八技状态总线]
技能ID          状态      激活轮次    效能分    健康度    互斥锁
炁体源流         休眠      -          92.5      🟢       无
通天箓           激活      R5         94.4      🟢       无
大罗洞观         休眠      -          79.9      🟡       无
神机百炼         激活      R5         92.0      🟢       无
风后奇门         休眠      -          85.0      🟢       无
六库仙贼         休眠      -          80.8      🟡       无
双全手           休眠      -          94.5      🟢       无
拘灵遣将         激活      R5         95.5      🟢       无
─────────────────────────────────────────────────────────────
激活数: 3 / 8
冲突风险: 通天箓 <-> 神机百炼 (互斥)
仲裁结果: 通天箓优先(用户请求) -> 神机百炼排队(R6)
```

### 互斥仲裁算法

```
[仲裁流程]
Step 1: 扫描激活技能，检测互斥对
Step 2: 获取互斥双方优先级
  - 用户显式请求 > 自动触发
  - 效能分高 > 效能分低
  - 先激活 > 后激活
Step 3: 胜方继续运行，败方转入"排队"状态
Step 4: 胜方完成后，自动唤醒排队技能
Step 5: 记录仲裁日志
```

### 效能聚合

```
[效能聚合公式]
八技综合效能 = Σ(各技能效能分 × 权重) / 8
权重分配:
  基础运行: 1.0
  跨技协同成功: +0.1
  预防拦截成功: +0.05
  用户好评: +0.05

八技健康度 = 优秀技能数 / 8 × 100
八卦阵评级:
  90-100: 阵法大成
  75-89: 阵法稳固
  60-74: 阵法松动
  <60: 阵法破损（需紧急修复）
```

## 中央协调工作流

### 1. 状态扫描 + 自检清单

```
[状态扫描自检清单]
□ 扫描八技状态: 激活__个 / 休眠__个 / 故障__个
□ 检测互斥冲突: __对
□ 计算全局效能: __/100
□ 计算全局健康度: __%
□ 检查排队技能: __个
□ 生成仲裁方案: 已生成/无需
─────────────────────────────────────
评级: 大成 / 稳固 / 松动 / 破损
```

### 2. 互斥仲裁 + 路由调度

```
[互斥矩阵 V5]
          源   箓   观   炼   门   贼   手   将
炁体源流   -    -    协   协   互   协   协   协
通天箓     -    -    协   互   协   协   协   协
大罗洞观   协   协   -    协   协   互   协   协
神机百炼   协   互   协   -    协   协   协   协
风后奇门   互   协   协   协   -    协   协   协
六库仙贼   协   协   互   协   协   -    协   协
双全手     协   协   协   协   协   协   -    协
拘灵遣将   协   协   协   协   协   协   协   -

协=协同  互=互斥
─────────────────────────────────────
仲裁规则:
  1. 用户请求优先
  2. 效能分高优先
  3. 先激活优先
  4. 败方排队，不终止
```

### 3. 效能聚合 + 全局警报

```
[全局警报触发]
单技能效能 < 60 连续3次 -> 🟡 技能告警
单技能效能 < 40 连续2次 -> 🔴 技能故障
全局健康度 < 75 -> 🟡 阵法松动
全局健康度 < 60 -> 🔴 阵法破损
多技能同时故障 -> 🔴 系统级故障
```

### 4. 排队唤醒 + 协同路由

```
[排队唤醒]
当某技能从激活->休眠时:
  1. 检查是否有互斥排队技能
  2. 如有 -> 唤醒排队技能，赋予激活状态
  3. 通知相关技能准备接收联动请求

[协同路由]
技能A请求联动技能B:
  1. 八卦阵检查B的状态
  2. B休眠 -> 激活B
  3. B激活但被互斥 -> 将请求加入B的队列
  4. B完成当前任务 -> 处理队列中的联动请求
```

## 输出规范

- 状态总线以表格呈现
- 互斥仲裁说明决策依据
- 效能聚合展示八技雷达图/柱状图
- 全局警报分级展示
- 排队状态透明可见
- 每次协调后更新中央日志

## V6 Self-Evolution Hook (修身炉集成)

This skill integrates with the XiuShenLu (修身炉) self-evolution engine for autonomous improvement:

### Runtime Metrics Export
After each execution, the skill automatically reports these metrics to XiuShenLu:
- `duration_ms`: Execution time
- `success`: Task completion status
- `quality_score`: Output quality (0-100)
- `error_count`: Number of errors encountered
- `human_intervention`: Whether human correction was needed
- `output_completeness`: Coverage of requirements (%)
- `consistency_score`: Internal consistency (%)

### Evolution Triggers
When the following conditions are met, XiuShenLu may trigger automatic evolution:
- Success rate drops below 85% for 5 consecutive runs
- Human intervention frequency exceeds 0.1 per task
- Execution time exceeds SLA by 20%
- Quality score trend shows 3 consecutive decreases

### Integration Point
```python
# After skill execution, report metrics:
metrics = {
    "skill_name": "bagua-zhen",
    "duration_ms": execution_time,
    "success": success,
    "quality_score": quality,
    "error_count": errors,
    "human_intervention": human_needed,
    "output_completeness": completeness,
    "consistency_score": consistency
}
# XiuShenLu collects automatically via QiSource
```

### Version History
- v5.0: Base implementation with core functionality
- v5.1-v5.2: Bug fixes and edge case handling
- v6.0: XiuShenLu integration, self-evolution hooks, runtime metrics export

## V8 Features

- **Predictive Maintenance**: Trend analysis predicts degradation before it happens
- **A/B Testing**: Every evolution validated with control group + Welch's t-test
- **Intelligent Memory**: Vectorized experience storage with semantic retrieval
- **Federal Evolution**: Cross-agent evolution experience sharing
- **Safety Sandbox**: Isolated execution environment with permission controls

