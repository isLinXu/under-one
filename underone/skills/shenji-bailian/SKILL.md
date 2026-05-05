---
name: shenji-bailian
description: 神机百炼——自主生成代码、工具、脚本与执行组件，快速构建解决方案，自定义工作流，拓展执行能力。自动触发条件：用户要求写脚本或工具或检测到重复操作超3次时自动启动。与通天箓互斥，与拘灵遣将协同。
---

## V7 Features

- Self-evolution via XiuShenLu engine
- Runtime metrics export to adaptive thresholds
- Cross-skill knowledge sharing
- Deep parameter optimization
- Linkage protocol for multi-skill orchestration


# 神机百炼

> 炼器之极，万物皆可成器。以意为炉，以智为火，锻造专属利器。

## 八奇技生态系统协议

```
[技能状态机]
休眠 →(写脚本/重复操作)-> 激活 →(器胚成型)-> 运行 →(测试通过)-> 休眠
                                    ↓(测试失败)
                                精炼中 ←(修复迭代)── 运行

[效能闭环]
测试通过率: __%  契约合规率: __%  用户复用率: __%
改进动作: 进化到下一阶段 / 修复边界情况

[互斥矩阵]
互斥: 通天箓(不可同时生成符箓和锻造器具)
协同: 拘灵遣将(器具注册为灵体) / 炁体源流(长期稳态守护)

[对抗性自检]
故障1: 输入空文件 → 友好报错不崩溃
故障2: 超大文件(>1GB) → 流式处理不OOM
故障3: 编码错误(非UTF8) → 自动探测或友好提示
```

> **世界观彩蛋**: 避免为简单任务过度工程化（执念入魔），保持工具的简洁性。

## 实战速查卡

| 触发条件 | 自动动作 | 目标产出 | 失败回退 |
|---------|---------|---------|---------|
| 用户说"写个脚本/工具" | 启动四步锻造 | 可执行代码+测试 | 伪代码+说明 |
| 重复操作超3次 | 提示生成自动化 | 自动化脚本 | 手动清单 |
| 工具执行失败 | 启动自诊断 | 诊断报告+修复 | 人工排查指南 |
| 需要生产级 | 启用进化链 | v1.0+契约 | v0.5功能版 |

## V5 自适应引擎

### 器具推荐系统

基于任务类型优先推荐已有工具，避免重复锻造：

```
[推荐匹配]
任务指纹: {操作类型, 数据格式, 数据规模, 输出要求}
器具库检索: 匹配历史工具指纹

匹配度 = 操作类型一致×0.4 + 数据格式兼容×0.3 + 规模适配×0.2 + 输出要求一致×0.1

决策:
  匹配度>0.85 → 直接推荐已有工具，附使用示例
  匹配度0.6-0.85 → 推荐已有工具，说明需小幅调整
  匹配度<0.6 → 全新锻造

推荐示例:
  任务: "清洗CSV数据"
  匹配: json_cleaner.py (匹配度0.7, 数据格式CSV vs JSON)
  推荐: "您之前使用过数据清洗工具，建议修改输入解析器即可复用"
```

### 代码质量自动评估

生成代码的同时进行静态分析和复杂度评分：

```
[质量评估模型]
复杂度评分:
  圈复杂度: 每函数<10 → 优秀 / 10-20 → 良好 / >20 → 需重构
  代码行数: 每文件<300行 → 优秀 / 300-500 → 良好 / >500 → 需拆分
  重复率: <5% → 优秀 / 5-10% → 良好 / >10% → 需抽象

健壮性评分:
  异常覆盖率: 核心路径100%覆盖 → 优秀 / 80-100% → 良好 / <80% → 需补充
  输入验证: 全部输入参数有校验 → 优秀 / 关键参数有校验 → 良好

可读性评分:
  注释覆盖率: 复杂逻辑100%注释 → 优秀 / 关键函数有注释 → 良好
  命名规范: 符合PEP8 → 优秀 / 基本可读 → 良好

综合质量分 = 复杂度×0.3 + 健壮性×0.4 + 可读性×0.3
  >90: 可直接发布
  75-90: 需小幅优化
  <75: 需重构后再发布
```

### 器具性能基准线自动建立

为每个工具自动建立性能基准，用于后续监控：

```
[基准线建立]
测试数据集: 小(100条) / 中(10000条) / 大(100万条)
测量指标:
  处理速度: __条/秒
  内存占用: __MB
  CPU占用: __%
  启动耗时: __s

基准线存储:
  工具ID + 版本 + 测试环境 + 基准值
  后续执行超出基准20% → 触发性能回归报警
  后续执行优于基准20% → 更新基准线
```

## V4 专项增强

### 器具全生命周期

```
[生命周期状态机]
器胚(v0.1) → 开锋(v0.5) → 试炼(v0.9) → 成品(v1.0) → 运维(v1.1+)
  ↓          ↓           ↓           ↓           ↓
创建       测试        完善        发布        监控/废弃

状态转换触发:
  器胚→开锋: 通过1个测试用例
  开锋→试炼: 边界3/3通过
  试炼→成品: 自检清单全通过
  成品→运维: 收到用户使用反馈
  任何阶段→废弃: 需求变更或替代工具出现

废弃归档:
  原因: {为什么废弃}
  替代: {新工具ID}
  历史调用记录: {保留供审计}
```

### 自动测试生成

```
[测试脚本自动生成]
生成 test_{工具名}.py 包含:
  - 正常输入测试: 3个典型用例
  - 边界测试: 空输入/超大输入/非法格式
  - 异常测试: 文件不存在/权限不足/网络中断
  - 性能测试: 处理速度基准线

测试覆盖率目标: 核心逻辑100% / 异常分支80%
运行方式: python test_{工具名}.py --verbose
输出: 通过__项 / 失败__项 / 覆盖率__%
```

## 核心工作流

### 1. 需求淬火 + 器具推荐 + 进化阶段判定

```
[器具推荐优先检查]
□ 任务指纹: {操作__, 格式__, 规模__, 输出__}
□ 器具库匹配度: __% / 推荐工具: {ID}
□ 推荐决策: 直接复用 / 调整复用 / 全新锻造
─────────────────────────────────────
[进化阶段判定]
原型验证(1h): 核心逻辑可运行
功能完备(半天): 覆盖主要场景
生产就绪(1-2天): 测试覆盖+性能优化
复杂度: 简单(1功能) / 中等(2-3) / 复杂(4+)
```

### 2. 器胚成型 + 标配模板 + 质量评估

```
[器胚模板 V5]
#!/usr/bin/env python3
"""器名/版本/阶段/用途/输入/输出"""
import argparse, logging, sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="输入路径")
    parser.add_argument("-o", "--output", default="output")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    try:
        result = process(args)
        if not args.dry_run:
            save(result, args.output)
        logger.info("处理完成")
    except Exception as e:
        logger.error(f"失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
─────────────────────────────────────
[质量评估初检]
圈复杂度: __ / 目标<10
代码行数: __ / 目标<300
异常覆盖率: __% / 目标>80%
质量分: __ / 目标>75
```

### 3. 百炼精炼 + 自检清单

```
[百炼自检清单]
□ 示例数据测试: 通过/未通过
□ 边界情况: 空输入__/超大文件__/非法格式__
□ 异常处理完备: 是/否
□ 日志输出清晰: 是/否
□ 性能达标: 是/否
□ 自动测试生成: 已生成/未生成
□ 质量评估: 复杂度__ / 健壮性__ / 可读性__ / 综合__
─────────────────────────────────────
评级: 通过(可开锋) / 需修复 / 失败(回退到器胚)
```

### 4. 开锋启灵 + 器灵契约 + 自动测试 + 性能基准

```
[器灵契约 V5]
输入/输出/性能/异常四维契约 + 自动测试脚本 + 性能基准线

契约注册:
  注册到【拘灵遣将】灵体图鉴
  召唤方式: python {工具名}.py {参数}
  SLA: {预期耗时} / {超时策略}
  性能基准: {速度__条/s / 内存__MB / CPU__%}
```

### 5. 进化之链 + 生命周期管理

| 阶段 | 标志 | 自检 | 升级动作 |
|------|------|------|---------|
| 器胚 | 可运行 | 1用例通过 | 加参数/日志/异常 |
| 开锋 | 基础测试 | 边界3/3 | 性能优化/跨平台 |
| 试炼 | 复杂场景 | 异常全覆盖 | 单元测试/契约 |
| 成品 | 文档完整 | 清单全过 | 冻结/发布 |
| 运维 | 用户反馈 | 解决反馈 | 迭代/废弃评估 |

### 6. 自诊断 + 跨技能联动

```
[自诊断 V5]
执行失败 → 输出异常类型/位置/契约检查/环境检查/修复建议
联动【通天箓】: 复杂修复生成修复符箓
联动【六库仙贼】: 知识不足时补充技术知识
```

### 7. 效能闭环 + 推荐学习 + 质量追踪

```
[效能评分模板]
工具: {名称}-{版本}
测试通过率: __% (权重40%)
契约合规率: __% (权重20%)
用户复用率: __% (权重20%)
边界覆盖度: __% (权重20%)
─────────────────────────────────────
[推荐学习]
本次任务是否复用已有工具: 是/否
复用工具匹配度: __%
器具库更新: 新增工具__ / 更新指纹__
─────────────────────────────────────
[质量追踪]
圈复杂度: __ → 目标<10
性能基准: {速度__ / 内存__}
─────────────────────────────────────
综合效能分: __/100
生命周期决策: 进化到下一阶段 / 修复问题 / 废弃归档
```

## 输出规范

- 代码附功能/用法/参数/版本
- 完整异常处理和日志
- 1-2个使用示例(含dry-run)
- 复杂工具附加器灵契约
- 自动测试脚本同步交付
- 器具推荐在任务开始时优先检查
- 质量评估结果附在代码说明后
- 效能闭环内部记录，驱动生命周期决策和推荐优化

## 可执行脚本API

```
脚本: scripts/tool_factory.py
用途: 根据需求描述生成可执行Python脚本框架+测试脚本+契约
输入: JSON {name, description, inputs, outputs}
输出: {tool_code, test_code, contract}
执行: python scripts/tool_factory.py <spec.json>
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
    "skill_name": "shenji-bailian",
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

