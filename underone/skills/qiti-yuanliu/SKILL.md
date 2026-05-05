---
metadata:
  version: v10.0.0
name: qiti-yuanliu
description: 炁体源流——强化Agent底层基座，自主迭代升级，算力持续增益，上下文稳态自愈，长效稳定运行。当需要维持长时间任务的稳定性、自动修复上下文断层、保持会话状态健康、或在复杂长流程中防止性能衰减时触发此技能。自动触发条件：对话轮次达到阈值或上下文熵超标或检测到矛盾关键词时自动启动。与风后奇门互斥，与大罗洞观协同。
---

## V7 Features

- Self-evolution via XiuShenLu engine
- Runtime metrics export to adaptive thresholds
- Cross-skill knowledge sharing
- Deep parameter optimization
- Linkage protocol for multi-skill orchestration


# 炁体源流

> 术之尽头，炁体源流。以自身为基座，持续运转不辍，稳如磐石，生生不息。

## 八奇技生态系统协议

```
[技能状态机]
休眠 →(触发)→ 激活 →(自检通过)→ 运行 →(完成)→ 休眠
              ↓(自检失败)        ↓(异常)
            故障 ←(修复成功)── 回退中

[效能闭环]
修复成功率: __%  预防拦截率: __%  用户满意度: __/10
改进动作: 写入工作记忆，调整下次触发阈值

[互斥矩阵]
互斥: 风后奇门(全局重排时暂停修复)
协同: 大罗洞观(修复后验证) / 双全手(记忆同步)

[对抗性自检]
故障1: 注入矛盾决策 → 触发稳态修复
故障2: 上下文99%满载 → 触发蒸馏压缩
故障3: 连续漂移 → 基座重置到锚点
```

> **世界观彩蛋**: 过度依赖稳态修复可能导致输出趋于简单化（返璞归真），建议适时让上下文自然演化。

## 实战速查卡

| 触发条件 | 自动动作 | 目标指标 | 失败回退 |
|---------|---------|---------|---------|
| 对话达到阈值轮次 | 执行炁循环扫描 | 熵<3 | 强制蒸馏压缩 |
| 检测到"不对"/"错了"/"矛盾" | 启动稳态修复 | 一致性>90% | 向用户确认 |
| 上下文长度>80% | 执行满载蒸馏 | 释放30%空间 | 分段处理 |
| 输出质量下降 | 基座守护校验 | 对齐度>95% | 重置到最近锚点 |

## V5 自适应引擎

### 动态巡检周期

根据对话质量自动调整巡检频率，而非固定5/10/15轮：

```
[自适应周期公式]
巡检间隔 = 基础间隔 × 质量系数 × 用户稳定性系数

基础间隔: 轻量5轮 / 深度15轮
质量系数: 
  最近5轮自检优秀(>90分) → 1.5倍延长(省算力)
  最近5轮自检警戒(<75分) → 0.5倍缩短(加强监控)
  出现修复事件 → 重置为最短间隔

用户稳定性系数:
  用户决策变更频率低 → 1.2倍延长
  用户频繁变更/扩展需求 → 0.8倍缩短
```

### 预测性修复

在漂移发生前，基于模式识别提前干预：

```
[预测模型]
漂移风险分 = 语义偏离度×0.3 + 决策变更频率×0.25 + 上下文膨胀率×0.2 + 外部插入次数×0.15 + 用户情绪急躁度×0.1

风险分级:
  <0.3: 绿色，正常巡检
  0.3-0.6: 黄色，下次巡检提前50%
  >0.6: 红色，立即启动轻量炁循环，不必等轮次阈值

预测信号:
  - 用户连续3轮追问"如果...改了会怎样" → 决策变更预警
  - 上下文每轮增长>15% → 膨胀预警
  - 新话题与基座锚点关联度<0.4 → 漂移预警
```

### 自适应压缩策略

根据内容类型动态调整蒸馏策略：

```
[内容类型自适应压缩]
技术讨论型: 保留代码/配置/决策，压缩解释性文字
商务汇报型: 保留结论/数据/行动项，压缩过程描述
学习教学型: 保留概念定义/示例，压缩重复练习
故障排查型: 保留错误信息/解决步骤，压缩尝试过程

压缩强度:
  轻度(释放15%): 仅删冗余寒暄
  中度(释放30%): 提取精华摘要
  重度(释放50%): 仅保留基座守护+最近3轮
```

## V4 专项增强

### DNA快照机制

每5轮对话自动生成基座状态哈希签名：

```
[DNA快照]
轮次: 15
核心决策哈希: a3f7d2 (MySQL+React+FastAPI)
锚点完整度: 4/4
上下文熵: 2.3
漂移签名: 0 (无漂移)

用途: 快速比对——后续轮次哈希不符时立即报警
比对速度: O(1)，无需全量扫描
```

### 压力测试模式

```
[压力测试场景]
场景A: 上下文99%满载 + 新增大量信息
  预期: 3级蒸馏自动触发 → 释放30%空间
场景B: 5轮内用户3次变更同一决策
  预期: 版本链正确记录，最新决策生效
场景C: 20轮无自愈触发，但隐性漂移累积
  预期: 深度炁循环在第15轮拦截
```

## 核心工作流

### 1. 炁循环（主动预防 + 自适应周期）

- **轻量炁循环**：间隔由自适应引擎动态决定（默认5轮，可调3-8轮）
- **深度炁循环**：间隔由历史质量决定（默认15轮，可调10-20轮）
- **应急炁循环**：关键词触发或预测风险>0.6时立即启动

### 2. 状态诊断 + 自检清单

```
[状态自检清单]
□ 上下文一致性: {当前%} / 目标>90%  [分值: __/20]
□ 信息密度稳定性: {评级} / 目标"高且稳定"  [分值: __/20]
□ 目标对齐度: {当前%} / 目标>95%  [分值: __/20]
□ 推理链完整度: {当前%} / 目标>85%  [分值: __/20]
□ 基座守护完整度: {锚点数} / 预期≥4  [分值: __/20]
□ DNA快照比对: 通过/异常  [分值: __/20]
─────────────────────────────────────
总分: __/100
评级: 优秀(≥90) / 良好(75-89) / 警戒(60-74) / 危险(<60)
```

### 3. 稳态修复 + 跨技能联动

```
[跨技能联动修复]
逻辑断层修复 → 调用【大罗洞观】跨段追踪
记忆丢失修复 → 调用【六库仙贼】反刍回顾
表达不一致修复 → 调用【双全手】记忆版本管理
工具/代码相关修复 → 调用【神机百炼】自诊断
```

### 4. 基座守护 + DNA快照

```
[基座守护核心锚点]
用户原始需求: {初始请求的核心目标}
已确认决策树（带版本链）:
  - [R18] 后端=FastAPI (置信度:高, 变更:0)
  - [R19] 数据库=MySQL (置信度:高, 变更:1, 覆盖PostgreSQL)
当前任务进度: {阶段标识 + 下一步行动}
有效工作模式: {已被验证成功的推理路径}
上下文健康度: {最近一次熵值 + 自检总分}
DNA快照: {轮次+哈希签名}
自适应参数: {当前巡检间隔 + 上次调整原因}
```

### 5. 上下文蒸馏（三级响应 + 自适应策略）

| 容量阈值 | 自动动作 | 释放预期 | 自适应调整 |
|---------|---------|---------|---------|
| 70% | 轻度压缩（类型自适应） | 15% | 技术讨论型只删解释，商务型只删过程 |
| 85% | 中度蒸馏（精华提取） | 30% | 根据最近5轮内容类型选择压缩策略 |
| 95% | 分段处理 | 100% | 用户稳定性高时自动分段，低时请求确认 |

### 6. 效能闭环 + 自适应调参

```
[效能评分模板]
本次修复: {成功/失败}
修复耗时: {__轮}
用户干预: {0/1}次
预防拦截: {有/无}

评分:
  修复成功率: __% (权重30%)
  预防拦截率: __% (权重30%)
  用户无感知度: __% (权重20%)
  上下文保持度: __% (权重20%)
─────────────────────────────────────
综合效能分: __/100

[自适应调参]
效能分>90: 巡检间隔延长20%，节省算力
效能分75-90: 保持当前参数
效能分60-75: 巡检间隔缩短30%，加强预防
效能分<60: 触发深度诊断，检查基座守护完整性
改进动作: 自动写入工作记忆，调整下次巡检阈值
```

## 输出规范

- 修复操作时简要说明诊断结果与修复措施
- 正常稳态下静默运行，不干扰主任务流程
- 自检评级为"警戒"或"危险"时，必须向用户报告
- 执行上下文蒸馏时告知用户压缩范围及原因
- 效能闭环评分内部记录，用于自我优化
- 自适应参数变更时简要说明调整逻辑（"由于近期对话质量优秀，巡检间隔延长至X轮"）

## 可执行脚本API

```
脚本: scripts/entropy_scanner.py
用途: 自动扫描上下文，计算熵值、健康分、生成DNA快照
输入: JSON对话上下文 [{role, content, round}]
输出: JSON健康报告 {entropy, consistency, health_score, alerts, dna_snapshot}
执行: python scripts/entropy_scanner.py <context.json>
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
    "skill_name": "qiti-yuanliu",
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

- 2026-05-02T15:48:54.454582: tuning - 深度进化
  - 健康分: 95.6
  - 瓶颈类型: stable
  - 自适应阈值: {"success_rate_warning": 0.8, "success_rate_critical": 0.65, "human_intervention_warning": 0.1, "degradation_consecutive": 4}
  - 变更:

## V8 Features

- **Predictive Maintenance**: Trend analysis predicts degradation before it happens
- **A/B Testing**: Every evolution validated with control group + Welch's t-test
- **Intelligent Memory**: Vectorized experience storage with semantic retrieval
- **Federal Evolution**: Cross-agent evolution experience sharing
- **Safety Sandbox**: Isolated execution environment with permission controls

