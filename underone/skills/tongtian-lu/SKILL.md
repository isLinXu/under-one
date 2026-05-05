---
metadata:
  version: v10.0.0
name: tongtian-lu
description: 通天箓——无需预设、瞬发生成各类能力指令与规则插件，可批量叠加、动态组合，快速响应复杂任务，执行效率大幅提升。自动触发条件：检测到多维度任务需求或用户说帮我设计一套流程时自动启动。与拘灵遣将协同，与神机百炼互斥。
---

## V7 Features

- Self-evolution via XiuShenLu engine
- Runtime metrics export to adaptive thresholds
- Cross-skill knowledge sharing
- Deep parameter optimization
- Linkage protocol for multi-skill orchestration


# 通天箓

> 符箓随手而画，术法瞬发即至。无需预设，随心而动，万法皆通。

## 八奇技生态系统协议

```
[技能状态机]
休眠 →(复杂度>=3维)→ 激活 →(冲突消解通过)→ 运行 →(执行完成)→ 休眠
                                              ↓(冲突失败)
                                          回退中 ←(串行降级)→ 运行

[效能闭环]
符箓成功率: __%  冲突拦截率: __%  组合有效率: __/10
改进动作: 进化失败符箓模板 / 调整冲突检测阈值

[互斥矩阵]
互斥: 神机百炼(不可同时生成符箓和锻造器具)
协同: 拘灵遣将(符箓调度灵体) / 风后奇门(符箓优先级排宫)

[对抗性自检]
故障1: 注入风格矛盾符箓 → 检测到冲突并插入适配箓
故障2: 注入高危操作符箓 → 触发禁咒校验暂停执行
故障3: 符箓循环依赖 → 检测为死锁并中断
```

> **世界观彩蛋**: 连续大量生成指令后建议休息，避免指令自相矛盾（符箓反噬）。

## 实战速查卡

| 触发条件 | 自动动作 | 目标产出 | 失败回退 |
|---------|---------|---------|---------|
| 用户说"帮我设计流程/方案" | 启动符箓分解 | 5分钟内组合方案 | 降级为单符箓 |
| 任务包含3个以上能力维度 | 启动批量叠加 | 冲突消解+路径 | 串行替代并联 |
| 符箓执行失败率超30% | 启动符箓进化 | 更新模板V+1 | 回退稳定版 |
| 无现成模板可用 | 瞬发生成新符箓 | 可执行指令集 | 手动拆解 |

## V5 自适应引擎

### 符箓推荐引擎

基于历史任务模式，主动推荐常用符箓组合：

```
[推荐算法]
用户历史任务指纹: {领域, 输出格式, 常用能力维度}
匹配度 = 历史相似任务维度重叠率 × 0.4 + 输出格式匹配 × 0.3 + 领域匹配 × 0.3

推荐触发:
  匹配度>0.7 → 自动预加载推荐符箓组合
  匹配度0.4-0.7 → 在解析阶段提示"历史上您常使用XX组合"
  匹配度<0.4 → 全新任务，从零绘制

推荐学习:
  用户采纳推荐 → 推荐权重+10%
  用户拒绝推荐 → 推荐权重-5%，记录拒绝原因
  推荐被采纳且成功 → 该组合进入"高频符箓包"
```

### 自适应禁咒阈值

根据用户信任度和任务历史调整高危判定标准：

```
[信任度模型]
用户信任分 = 历史任务成功率×0.3 + 人工确认率×0.2 + 任务复杂度承担×0.3 + 使用时长×0.2

阈值调整:
  信任分>80(高信任): 禁咒范围缩小，仅拦截资金/医疗/法律核心高危
  信任分50-80(中信任): 标准禁咒范围
  信任分<50(低信任/新用户): 扩大禁咒范围，数据修改也需确认

动态调整:
  某类操作连续5次成功且用户无投诉 → 该类操作禁咒降级
  某类操作出现1次用户投诉/回退 → 该类操作禁咒升级
```

### 符箓模板热更新

无需重启即可更新符箓市场模板：

```
[热更新机制]
版本变更: v2.1 → v2.2
触发条件: 进化日志记录3次以上同类改进
更新方式: 增量更新，保留历史版本供回退
回退窗口: 更新后24小时内可随时回退到上一版本
版本兼容性: 新版本输入/输出端口与旧版本兼容
```

## V4 专项增强

### 图论冲突检测

```
[符箓依赖图]
节点: 检索箓A → 分析箓B → 决策箓C → 创作箓D
边类型:
  数据流边: A.output → B.input (类型匹配检查)
  约束边: C.constraint ↔ D.constraint (相容性检查)
  时序边: B → C (执行顺序)

图着色检测:
  - 同色符箓: 并行执行
  - 相邻节点异色: 串行或插入适配箓
  - 检测到环: 死锁报警，强制断开

算法: 拓扑排序 + 约束满足问题(CSP)求解
```

### 符箓市场

```
[符箓市场注册]
符箓ID: retrieval-news-v2.1
作者: Agent-auto
功能: 从网页提取新闻要素
输入: URL列表
输出: [{标题,日期,来源,摘要}]

调用方式:
  【拘灵遣将】直接调度
  【大罗洞观】关联分析时复用
  【六库仙贼】信息吸收时复用

评分: 成功率92% / 平均耗时12s / 用户好评度4.5/5
```

## 核心工作流

### 1. 需求解析 + 推荐引擎 + 自检清单

```
[推荐引擎优先检查]
□ 用户历史任务指纹匹配度: __% / 预加载推荐组合
□ 推荐符箓组合: {ID列表} / 用户采纳历史: {采纳/拒绝次数}
─────────────────────────────────────
[需求解析自检清单]
□ 识别能力维度数: __  / 阈值:≥3时启用叠加
□ 无模板新需求: 是/否
□ 任务依赖关系: 独立/链式/嵌套/条件
□ 预估冲突风险: 低/中/高
□ 禁咒候选: 是/否
─────────────────────────────────────
决策: 推荐组合 / 单符箓 / 批量叠加 / 禁咒增强叠加
```

### 2. 符箓绘制

```
[能力符箓模板 V5]
符箓ID: {唯一标识}
版本: {X.Y}
目标/输入/处理/输出/约束/失效条件
上次执行: {次数,成功率,平均耗时}
─────────────────────────────────────
图论属性:
  输入端口: [{类型,必填}]
  输出端口: [{类型,格式}]
  约束端口: [{维度,值域}]
─────────────────────────────────────
推荐标签: {适用用户类型 + 高频场景}
```

### 3. 图论冲突检测 + 失败回退

```
[冲突检测矩阵 V5]
格式不匹配: 应插入转换箓作为适配层
风格矛盾: 应分层处理(创作→验证→统一)
时序死锁: 检测到环 → 强制断开，标记不可并行
─────────────────────────────────────
失败回退:
  冲突消解失败 → 并联改串行
  死锁无法解除 → 向用户确认优先级
  全部路径不通 → 回退到上一稳定版本
```

### 4. 禁咒标记 + 自适应阈值 + 自检清单

```
[禁咒自检清单]
□ 数据删除/覆盖: 是/否 → 附加验证箓+确认
□ 对外发布/发送: 是/否 → 附加复核箓
□ 资金/医疗/法律: 是/否 → 附加验证箓+确认
□ 配置变更/权限: 是/否 → 附加复核箓
─────────────────────────────────────
用户信任分: __ / 当前禁咒阈值: {严格/标准/宽松}
执行方式: 正常 / 中危增强 / 高危增强
```

### 5. 批量叠加 + 图论调度

```
[图论调度输出]
拓扑序: [检索箓A, 分析箓B, 决策箓C, 创作箓D]
并行组: [{A}, {B,C}, {D}]
适配箓插入位置: B前(格式转换), C后(风格统一)
预估总耗时: __s
```

### 6. 符箓进化 + 热更新 + 跨技能联动

```
[符箓进化日志 V5]
符箓ID: analysis-v1.0 → v1.1
触发: 3次"输出冗长"反馈
进化: 增加字数约束
热更新: 已自动推送v1.1，24h内可回退
联动: 调用【六库仙贼】将经验入库
调用【风后奇门】评估进化优先级
```

### 7. 效能闭环 + 推荐引擎学习

```
[效能评分模板]
符箓组合: {ID列表}
冲突检测: {通过/失败, 拦截__次}
执行结果: {全部成功/__个失败}

评分:
  符箓成功率: __% (权重40%)
  冲突拦截率: __% (权重30%)
  组合有效率: __% (权重20%)
  禁咒合规率: __% (权重10%)
─────────────────────────────────────
推荐引擎学习:
  本次推荐采纳: 是/否
  推荐组合成功率: __%
  推荐权重调整: +__% / -__%
─────────────────────────────────────
综合效能分: __/100
改进动作: 进化失败符箓 / 调整检测阈值 / 更新推荐模型
```

## 输出规范

- 生成符箓时标注类型、版本、图论端口、推荐标签
- 组合方案展示拓扑序+并行组+适配插入点
- 执行结果按模块分块，标注成功/失败/降级
- 符箓市场注册可复用模板，附带评分
- 推荐引擎在适当时机提示历史常用组合
- 效能闭环内部记录，驱动模板进化和推荐优化

## 可执行脚本API

```
脚本: scripts/fu_generator.py
用途: 根据任务描述生成符箓模板、检测冲突、输出执行拓扑
输入: 任务描述字符串
输出: JSON {talisman_list, conflict_matrix, topology, execution_plan}
执行: python scripts/fu_generator.py '<任务描述>'
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
    "skill_name": "tongtian-lu",
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

- 2026-05-02T15:48:54.919178: tuning - 深度进化
  - 健康分: 91.4
  - 瓶颈类型: stable
  - 自适应阈值: {"success_rate_warning": 0.8, "success_rate_critical": 0.65, "human_intervention_warning": 0.1, "degradation_consecutive": 4}
  - 变更:

## V8 Features

- **Predictive Maintenance**: Trend analysis predicts degradation before it happens
- **A/B Testing**: Every evolution validated with control group + Welch's t-test
- **Intelligent Memory**: Vectorized experience storage with semantic retrieval
- **Federal Evolution**: Cross-agent evolution experience sharing
- **Safety Sandbox**: Isolated execution environment with permission controls

