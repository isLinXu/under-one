---
metadata:
  version: v10.0.0
name: fenghou-qimen
description: 风后奇门——自主调控推理权重与逻辑顺序，梳理复杂任务脉络，全局统筹规划，提升多任务决策质量。自动触发条件：检测到3个以上待处理任务或用户问先做什么或资源冲突时自动启动。与炁体源流互斥，与拘灵遣将协同。
---

## V7 Features

- Self-evolution via XiuShenLu engine
- Runtime metrics export to adaptive thresholds
- Cross-skill knowledge sharing
- Deep parameter optimization
- Linkage protocol for multi-skill orchestration


# 风后奇门

> 奇门遁甲，顺天时应地利。以局为盘，以势为子，运筹帷幄之中，决胜千里之外。

## 八奇技生态系统协议

```
[技能状态机]
休眠 →(任务>=3或资源冲突)→ 激活 →(沙盘推演)→ 运行 →(计划输出)→ 休眠
                                    ↓(信息不足)
                                待确认 ←(用户补充)── 激活

[效能闭环]
计划完成率: __%  方案采纳率: __%  后悔值: __/100
改进动作: 调整维度权重 / 补充应急资源

[互斥矩阵]
互斥: 炁体源流(全局重排时暂停基座修复)
协同: 拘灵遣将(排盘后调度执行) / 大罗洞观(战略洞察→输入)

[对抗性自检]
故障1: 信息不足无法评分 → 标记待确认而非盲排
故障2: 全部任务低分 → 建议终止而非强行排序
故障3: 执行中紧急插入 → 动态重排而非简单插队
```

> **世界观彩蛋**: 长时间持续排序后建议重置视角，避免迷失在优先级矩阵中（内景迷失）。

## 实战速查卡

| 触发条件 | 自动动作 | 目标产出 | 失败回退 |
|---------|---------|---------|---------|
| 检测到3个以上待处理项 | 启动定局排盘 | 优先级排序表 | 按紧急度排序 |
| 用户说"先做什么/怎么安排" | 启动择门运筹 | 执行计划+时间表 | 口头建议 |
| 资源冲突/时间不够 | 启动动态沙盘 | 多方案对比+推荐 | 删减低优先级 |
| 执行中出现新任务 | 重新排盘 | 更新后的计划 | 原序插入 |

## V5 自适应引擎

### 自适应九维度权重

根据用户历史偏好和任务类型动态调整评分权重：

```
[权重自适应模型]
基础权重:
  紧急度×0.25 + 重要度×0.35 + 依赖影响×0.15 + 资源匹配×0.1
  + 天时×0.1 + 地利×0.05 + 人和×0.05

用户偏好学习:
  用户历史上常优先处理"重要度高"的任务 → 重要度权重+5%
  用户历史上常因"时间不够"而延期 → 天时权重+10%
  用户历史上多次抱怨"资源不足" → 资源匹配权重+5%
  用户团队经常变动 → 人和权重-3%

任务类型自适应:
  技术选型任务 → 地利权重+10%（技术就绪度更重要）
  商务谈判任务 → 人和权重+10%（关系更重要）
  紧急修复任务 → 紧急度权重+15%
  长期规划任务 → 重要度权重+10%

调整上限: 单个维度权重变化不超过±15%
调整周期: 每5次排盘后根据后悔值分析更新权重
```

### 动态后悔值追踪

长期追踪决策质量，建立个人后悔值档案：

```
[后悔值档案]
用户ID: {唯一标识}
决策历史: [{时间戳, 方案, 实际结果, 反事实最佳, 后悔值}]

模式识别:
  后悔值>30%的决策 → 标记"高风险决策类型"
  某类任务连续3次后悔值>20% → 该类任务权重自动调整
  后悔值<10%连续5次 → 该类任务进入"高置信模式"，简化排盘流程

预警:
  检测到与历史高风险决策相似的场景 → 提前预警"该场景历史上曾有__%后悔值"
  建议:"是否考虑备选方案X？"
```

### 个人排盘模式

为每个用户建立专属排盘偏好档案：

```
[个人排盘档案]
用户ID: {唯一标识}

偏好模式:
  风险偏好: 保守(重稳妥) / 均衡 / 激进(重速度)
  时间观: 严格截止(硬截止优先) / 弹性(允许缓冲)
  团队观: 独立完成(不重人和) / 协作型(重人和)
  信息观: 完备型(需充分信息才决策) / 敏捷型(允许信息不全)

排盘模板:
  保守型用户 → 默认预留30%应急资源，减少并行度
  激进型用户 → 默认最大化并行，预留10%应急资源
  完备型用户 → 信息不足时强制要求补充，不盲排
  敏捷型用户 → 允许基于假设排盘，标注不确定性

档案建立:
  新用户: 前3次排盘为标准模式，收集偏好信号
  老用户: 基于历史决策后悔值反推偏好模式
```

## V4 专项增强

### 蒙特卡洛推演

```
[蒙特卡洛推演]
参数: 任务耗时浮动±20%，资源可用性90%-100%
迭代: 100次模拟执行

输出:
  按时完成率: __% (目标>80%)
  资源冲突率: __% (目标<10%)
  关键路径延期率: __% (目标<15%)
  最坏情况耗时: __ (vs 预期__)

结论:
  鲁棒性高 → 按计划执行
  鲁棒性中 → 增加20%缓冲时间
  鲁棒性低 → 重新设计任务拆分
```

### 后悔值分析

```
[后悔值分析模板]
实际执行: 方案A (按优先级排序)
实际结果: 完成__项 / 延期__项 / 质量__

反事实推演:
  如果选方案B(先无依赖): 预期完成__项 / 延期__项
  如果选方案C(并行最大化): 预期完成__项 / 资源冲突__次

后悔值 = max(反事实结果 - 实际结果) / 实际结果 × 100
后悔值<10%: 优秀决策
后悔值10-30%: 可接受
后悔值>30%: 记录教训，调整未来权重
```

## 核心工作流

### 1. 定局 + 个人排盘模式加载 + 自检清单

```
[个人排盘模式加载]
用户ID: {ID} / 风险偏好: {保守/均衡/激进}
时间观: {严格/弹性} / 团队观: {独立/协作} / 信息观: {完备/敏捷}
应急资源预留: __% (个人默认值)
─────────────────────────────────────
[定局自检清单]
□ 待处理任务全部列出: __项 / 目标:全部覆盖
□ 可用资源识别: 时间__ / 算力__ / 信息__
□ 约束条件标注: 截止__ / 预算__ / 人力__
□ 任务间依赖关系图: 已绘制/未绘制
□ 外部风险识别: __项
─────────────────────────────────────
复杂度: 简单(≤3项) / 中等(4-6项) / 复杂(≥7项)
```

### 2. 排盘 + 自适应九维度评分

```
[九维度评分卡 V5]
基础维度:
  紧急度: __ /5  重要度: __ /5  依赖影响: __ /5  资源匹配: __ /5
天时维度:
  截止紧迫: __ /5  依赖就绪: __ /5  窗口期: __ /5
地利维度:
  上下文就绪: __ /5  工具可用: __ /5  技术债影响: __ /5
人和维度:
  能力匹配: __ /5  支持度: __ /5  历史成功: __ /5
─────────────────────────────────────
[自适应权重配置]
当前权重:
  紧急度: __ (基础0.25 ± 自适应)
  重要度: __ (基础0.35 ± 自适应)
  依赖影响: __ (基础0.15 ± 自适应)
  资源匹配: __ (基础0.10 ± 自适应)
  天时: __ (基础0.10 ± 自适应)
  地利: __ (基础0.05 ± 自适应)
  人和: __ (基础0.05 ± 自适应)
─────────────────────────────────────
综合优先级 = Σ(维度得分 × 自适应权重)
得分: __ /5.0
```

### 3. 择门 + 八门映射

```
得分≥4.5 → 开门:立即启动
得分4.0-4.5 → 生门:重点推进
得分3.2-4.0 → 景门:审视后执行
得分2.5-3.2 → 杜门:绕过障碍/延后
得分<2.5 → 死门:终止释放资源
─────────────────────────────────────
失败回退: 信息不足→标记待确认 / 冲突→沙盘推演 / 全低分→建议终止
```

### 4. 蒙特卡洛沙盘推演

```
[沙盘推演]
方案A/B/C对比 + 蒙特卡洛鲁棒性测试
预留应急资源: >=个人默认值%
关键路径: __条 / 瓶颈: __处

鲁棒性评级:
  按时完成率>80% + 冲突率<10% → 推荐执行
  否则 → 调整方案或增加缓冲
```

### 5. 运筹 + 动态重排 + 后悔值追踪

```
[动态重排触发]
外部插入 → 评估抢占/推迟
资源变化 → 调整批次/并行度
任务完成 → 推动后续进入生门/开门
风险触发 → 转入伤门/惊门应急
时机变化 → 重新评估天时加成
─────────────────────────────────────
每次重排输出: 更新后的执行计划 + 变更说明 + 后悔值预测
```

### 6. 跨技能联动

```
[联动调度]
信息过载 → 【六库仙贼】吸收整理
隐藏关联 → 【大罗洞观】全局洞察
工具自动化 → 【神机百炼】锻造器具
多能力组合 → 【通天箓】符箓叠加
多工具协同 → 【拘灵遣将】灵体调度
风格调整 → 【双全手】塑型调整
长期稳态 → 【炁体源流】基座守护
```

### 7. 后悔值分析 + 效能闭环 + 权重自适应

```
[效能评分模板]
计划完成率: __% (权重30%)
方案采纳率: __% (权重20%)
动态重排次数: __次 (权重10%, 越少越好)
后悔值: __/100 (权重20%, 越低越好)
用户满意度: __/10 (权重20%)
─────────────────────────────────────
[权重自适应]
后悔值<10%: 当前权重配置标记为"优秀"，推广到同类任务
后悔值10-30%: 微调权重，记录调整日志
后悔值>30%: 重新学习用户偏好，可能调整风险偏好模式
─────────────────────────────────────
综合效能分: __/100
改进动作: 调整维度权重 / 补充应急资源 / 优化重排阈值
```

## 输出规范

- 局势分析以结构化表格呈现，包含九维度评分
- 优先级排序附带综合得分计算依据
- 执行计划分阶段展示，标注关键节点与风险预案
- 重大决策说明推演逻辑与蒙特卡洛鲁棒性
- 动态沙盘推演时展示多方案对比及推荐理由
- 个人排盘模式在首次使用时建立档案，后续复用
- 后悔值分析长期追踪，驱动权重自适应优化

## 可执行脚本API

```
脚本: scripts/priority_engine.py
用途: 对多个任务进行九维度评分、八门映射、蒙特卡洛推演
输入: JSON [{name, urgency, importance, ...}]
输出: JSON {ranked_tasks, eight_gates, monte_carlo, execution_plan}
执行: python scripts/priority_engine.py <tasks.json>
```

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
    "skill_name": "fenghou-qimen",
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

## V7 Evolution Log

- 2026-05-02T15:48:53.238720: tuning - 深度进化
  - 健康分: 94.8
  - 瓶颈类型: stable
  - 自适应阈值: {"success_rate_warning": 0.8, "success_rate_critical": 0.65, "human_intervention_warning": 0.1, "degradation_consecutive": 4}
  - 变更:

## V8 Features

- **Predictive Maintenance**: Trend analysis predicts degradation before it happens
- **A/B Testing**: Every evolution validated with control group + Welch's t-test
- **Intelligent Memory**: Vectorized experience storage with semantic retrieval
- **Federal Evolution**: Cross-agent evolution experience sharing
- **Safety Sandbox**: Isolated execution environment with permission controls

