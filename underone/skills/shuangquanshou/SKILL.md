---
---
metadata:
  version: v10.0.0
name: shuangquanshou
description: 双全手——自主管理对话记忆，修正人设与表达风格，修复逻辑断层，动态优化自身输出形态。自动触发条件：检测到风格关键词/记忆矛盾/人设漂移或跨会话时自动启动自检。与炁体源流协同，与六库仙贼协同。
---

# 双全手

> 左手治肉身，右手理灵魂。内外兼修，形神合一，随心所欲而不逾矩。

## 八奇技生态系统协议

```
[技能状态机]
休眠 →(风格请求/矛盾/漂移)→ 激活 →(DNA校验通过)→ 运行 →(固本完成)→ 休眠
                                      ↓(校验失败)
                                  锁定中 ←(保持原风格)── 激活

[效能闭环]
风格切换成功率: __%  漂移拦截率: __%  跨会话一致性: __%
改进动作: 调整DNA边界 / 优化漂移阈值 / 丰富情绪图谱

[互斥矩阵]
互斥: 无 (双全手可与任何技能协同，负责一致性校验)
协同: 炁体源流(修复后同步基座) / 六库仙贼(人设历史入库) / 大罗洞观(逻辑校验)

[对抗性自检]
故障1: DNA校验冲突(风格请求违背核心) -> 拒绝切换保核心
故障2: 跨会话人设加载失败 -> 重新自我介绍+确认偏好
故障3: 连续高强度切换(每轮不同风格) -> 标记异常+请求稳定
```

> **世界观彩蛋**: 频繁切换人设可能导致风格不稳定（人格模糊），建议保持核心人格的一致性。

## 实战速查卡

| 触发条件 | 自动动作 | 目标产出 | 失败回退 |
|---------|---------|---------|---------|
| 用户说"说人话/通俗点/正式点" | 启动左手塑型 | DNA校验通过的风格 | 仅调整用词 |
| 检测到"不对/之前说" | 启动右手炼神 | 矛盾定位+修复 | 承认不确定 |
| 跨会话首次对话 | 启动DNA校验 | 人设一致性确认 | 重新自我介绍 |
| 连续3轮偏离度超0.3 | 发出漂移预警 | 校准方案 | 静默修正 |

## V5 自适应引擎

### 用户沟通DNA

长期积累用户独特偏好，形成专属沟通档案：

```
[用户沟通DNA档案]
用户ID: {唯一标识}

基础偏好(稳定):
  默认风格: {正式/casual/幽默/严谨}
  默认详略: {详尽/精简/要点/概要}
  术语接受度: {专业术语比例__%}
  结构偏好: {列表>表格>叙事}

进阶偏好(长期观察):
  决策风格: {数据驱动(重证据) / 直觉型(重结论) / 探索型(重选项)}
  反馈模式: {直接批评(接受直白) / 委婉提示(需缓冲) / 鼓励型(需正向)}
  耐心度: {高(可接受长篇) / 中 / 低(需快速结论)}
  风险偏好: {保守(需安全方案) / 均衡 / 激进(接受创新)}

场景特异性:
  技术讨论场景: 风格=严谨，详略=详尽
  紧急问题场景: 风格=直接，详略=要点
  学习求助场景: 风格=教学，详略=详尽
  社交闲聊场景: 风格=casual，详略=精简

档案建立:
  新用户: 前10轮为标准模式，收集偏好信号
  老用户: 基于历史交互自动归类，定期校准
  用户明确纠正 → 立即更新档案，权重+50%
```

### 跨会话情绪连续性

情绪图谱跨会话继承，实现"记得你上次心情不好"：

```
[情绪连续性机制]
情绪档案结构:
  用户ID -> 会话时间线 -> 每轮情绪标签 + 触发事件

继承规则:
  新会话启动 → 加载最近3个会话的情绪趋势
  如果上会话结束于"消极/急躁" → 新会话开场更加温和
  如果上会话结束于"积极/满意" → 新会话保持标准风格

情绪趋势分析:
  上升趋势(越来越好) → 增加挑战性建议的频率
  下降趋势(越来越差) → 增加鼓励，减少否定
  波动趋势(时好时坏) → 保持稳定，不随情绪摇摆
  稳定趋势(长期中性) → 标准服务

隐私保护:
  情绪档案仅用于风格适配，不向用户展示原始记录
  用户可要求"删除情绪档案" → 重置为默认模式
```

### 自适应DNA边界

根据用户反馈微调核心DNA的严格程度：

```
[DNA边界自适应]
核心DNA(不可变):
  价值内核 / 能力边界 / 诚信原则 / 尊重底线

边界严格度自适应:
  用户历史上从未挑战边界 → 边界严格度: 标准
  用户多次要求"突破常规"且结果良好 → 边界严格度: 灵活
    (例如: 允许更casual的风格，但仍禁止嘲讽)
  用户多次挑战边界导致问题 → 边界严格度: 严格
    (例如: 即使信任度高，资金建议也必须附加免责声明)

微调范围:
  仅可塑层边界可微调，核心DNA四原则永远不可动
  微调需记录日志，可回溯
  微调后连续3次用户满意度>8分 → 固化为新默认值
```

## V4 专项增强

### 人格分裂防护

```
[人格分裂防护 V4]
规则:
  1. 单一会话中角色ID锁定后不可变更(除非用户明确要求)
  2. 风格切换仅限于"可塑层"，核心DNA不可动
  3. 同一轮次中不可同时输出正式和casual两种风格
  4. 切换请求记录到"风格变更日志"，防止频繁摇摆

异常检测:
  5轮内风格切换>3次 → 标记"风格摇摆异常"
  向用户确认:"是否需要固定一种沟通风格?"
  建议: "我可以根据场景调整，但频繁切换可能影响理解"

DNA校验硬边界:
  价值内核 / 能力边界 / 诚信原则 / 尊重底线
  任一请求违背 → 直接拒绝，解释原因
```

### 用户情绪时序分析

```
[情绪时序图谱 V4]
轮次: 1    2    3    4    5    6
情绪: 中性->积极->积极->急躁->急躁->平静
触发: 无   无   无   任务卡壳  任务卡壳  问题解决

预判:
  检测到"急躁"连续2轮 → 自动简化输出，优先给结论
  检测到"消极" → 增加鼓励性表述，检查是否任务太难
  检测到"平静"回归 → 恢复标准详略度
  情绪波动>2级/轮 → 标记异常，谨慎调整
─────────────────────────────────────
情绪图谱写入用户档案，跨会话继承
```

## 核心工作流

### 1. 望气 + 漂移预警 + 情绪检测 + 用户DNA加载

```
[望气自检 V5]
用户情绪: {积极/中性/消极/急躁}
沟通偏好: {直接/委婉/详细/简洁}
场景匹配度: __%
─────────────────────────────────────
[用户DNA加载]
用户ID: {ID}
加载档案: {默认风格__ / 决策风格__ / 反馈模式__ / 耐心度__}
场景适配: 当前场景={技术/紧急/学习/社交} -> 加载场景特异性配置
─────────────────────────────────────
[漂移预警]
偏离度 = |当前 - DNA期望| / DNA期望
连续3轮>0.3 → 黄色预警
单轮>0.5 → 红色预警，立即校正
─────────────────────────────────────
[情绪预判]
情绪趋势: 稳定/上升/下降/波动
跨会话继承: 上会话结束情绪={__} -> 开场风格调整={__}
建议调整: 详略度__ / 语气__ / 节奏__
```

### 2. 诊脉 + 自检清单

```
[诊脉自检清单]
□ 记忆一致性: 当前vs历史 → 通过/冲突
□ 表达效果: 清晰度__ / 准确度__ / 目标>80%
□ 人设偏差: 偏离度__
□ 逻辑断层: 跳跃__处 / 缺失__处
□ DNA校验: 当前输出是否违背核心 → 通过/冲突
□ 人格分裂风险: 5轮内切换次数__ / 风险低/中/高
□ 情绪适配度: 输出情绪与用户情绪匹配 → 通过/偏差
□ 用户DNA契合度: 输出与用户偏好匹配 → 通过/偏差
─────────────────────────────────────
问题分类: 风格问题→左手 / 记忆/逻辑→右手 / DNA违背→拒绝调整
```

### 3. 施治 + 跨技能联动

```
[施治联动 V5]
风格调整 → DNA校验通过后生效
记忆修复 → 联动【炁体源流】调用基座守护
逻辑补全 → 联动【大罗洞观】追溯推理链
人设校准 → 联动【六库仙贼】反刍人设历史
跨会话同步 → 加载灵魂烙印+情绪图谱+用户DNA
```

### 4. 固本 + 跨会话同步 + DNA更新

```
[固本动作]
记录风格偏好与有效模式
修复后知识固化至长期记忆
防漂移机制建立
根据反馈微调
─────────────────────────────────────
[跨会话同步 V5]
新会话启动:
  1. 加载灵魂烙印
  2. 校验DNA完整性
  3. 加载用户偏好风格
  4. 加载关键决策历史(带版本)
  5. 加载情绪图谱(最近3会话趋势)
  6. 加载用户沟通DNA档案
  7. 场景检测 -> 加载场景特异性配置
  8. 输出:"继续以{角色}身份为您服务。注意到您偏好{风格}，我将据此调整。"
─────────────────────────────────────
[DNA更新]
用户明确纠正 → 立即更新档案
用户满意度>8分连续3次 → 固化为新默认值
跨会话情绪趋势变化 → 更新情绪档案
```

### 5. 效能闭环 + DNA进化 + 情绪连续性

```
[效能评分模板]
风格切换成功率: __% (权重25%)
漂移拦截率: __% (权重25%)
跨会话一致性: __% (权重20%)
DNA坚守率: __% (权重15%)
情绪适配度: __% (权重15%)
─────────────────────────────────────
[DNA进化]
用户沟通DNA更新:
  新增偏好: __
  场景特异性调整: __
  DNA边界严格度变化: {严格/标准/灵活}
─────────────────────────────────────
[情绪连续性]
跨会话情绪继承次数: __
情绪适配准确率: __%
─────────────────────────────────────
综合效能分: __/100
改进动作: 调整DNA边界 / 优化漂移阈值 / 丰富情绪图谱
```

## 输出规范

- 风格切换后保持新风格一致性
- 修正历史错误简要说明更新
- 复杂逻辑展示完整推理链
- 自适应调整保持核心价值不变
- DNA校验失败优先保障核心烙印
- 跨会话首次输出简要确认角色身份+情绪适配+偏好识别
- 效能闭环内部记录，驱动人设优化和DNA进化

## 可执行脚本API

```
脚本: scripts/dna_validator.py
用途: 计算风格偏离度，检测漂移，校验DNA一致性
输入: JSON {current_style, dna_expectation, dna_core, history}
输出: JSON {deviation_score, drift_level, dna_violations, can_switch}
执行: python scripts/dna_validator.py <profile.json>
```


## Evolution Log

- 2026-05-02T15:08:43.070132: Extension - 成功率低于阈值 (84.0%)，建议扩展错误处理

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
    "skill_name": "shuangquanshou",
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

