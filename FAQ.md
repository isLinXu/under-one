# under-one.skills FAQ — 预期质疑与标准回应

> 基于GitHub开源社区的典型质疑模式准备的标准回答。建议维护者在Issues中直接引用。

---

## Q1: 八奇技只是名字包装吗？去掉名字还剩什么？

**直接回答**：不是包装。每个skill的核心机制是独立设计的，名字只是映射。

**具体说明**：
- 风后奇门的"九维度评分+八门映射" → 和奇门遁甲的"四盘八门"是**结构同构**，不是硬凑
- 六库仙贼的"六阶段消化管道" → 对应原著"六腑"的**功能映射**（胃纳→小肠分解→胆提纯）
- 拘灵遣将的"降级保护/服灵内化" → 对应"服灵"的**行为映射**（工具不可用时的两种策略）

**底线**：你可以把skill名称改成 `context-guard`、`priority-engine`、`tool-orchestrator`，功能完全一样。中文名是**文化注释**不是功能依赖。

---

## Q2: 这和 LangChain 有什么区别？

**一句话**：LangChain 解决"怎么连工具"，under-one.skills 解决"连了之后怎么不崩"。

**详细对比**：

| 场景 | LangChain 怎么做 | under-one.skills 怎么做 |
|------|-----------------|-----------------|
| 多工具调用 | `chain.run()` 串行执行 | 拘灵遣将：健康检查+降级保护+SLA监控 |
| 长对话漂移 | 无内置机制 | 炁体源流：熵计算+稳态修复 |
| 任务优先级 | 无内置机制 | 风后奇门：九维度评分+蒙特卡洛验证 |
| 人格一致性 | 靠prompt约束 | 双全手：DNA校验+风格漂移拦截 |

**关系**：互补。你可以在 LangChain 应用里 `import` under-one.skills 的脚本，两者不冲突。

---

## Q3: 能用于生产环境吗？

**诚实回答**：
- ✅ 可以作为**内部工具**用于生产（所有脚本可独立运行，无外部依赖）
- ⚠️ 作为**Python包**还不成熟（需要 `pip install under-one` 的封装，V11目标）
- ⚠️ 需要**真实LLM验证**（当前验证基于模拟负载，建议补充OpenAI/Claude实测）

**生产就绪度评估**：
```
独立脚本执行:     ████████████ 100%
错误处理完善:     ████████░░░░  70%  (部分脚本缺try/except)
配置外部化:       ██████░░░░░░  50%  (阈值部分硬编码)
CI/CD测试:        ░░░░░░░░░░░░   0%  (V11目标)
```

---

## Q4: 版权风险？

**现状**：
- "八奇技""炁体源流"等名称是《一人之下》的**作品元素**
- 本项目**未获得**版权方授权
- 当前是**MIT开源项目**，非商业产品

**风险评估**：
| 场景 | 风险 | 建议 |
|------|------|------|
| GitHub开源学习交流 | 极低 | 已加免责声明 |
| 个人/公司内部使用 | 低 | 默认许可范围内 |
| 商业化产品使用这些名称 | **中-高** | 建议改名 |
| 制作周边/收费课程 | **高** | 必须获得授权 |

**应急预案**：
如果收到版权方联系，立即：
1. 仓库改名为 `agent-octaves` 或 `skill-forge`
2. skill内部名称改为英文（context-guard, priority-engine等）
3. 中文名作为别名保留在注释中
4. 代码和功能完全不变

---

## Q5: 修身炉的自进化是伪需求吗？

**直接回答**：对1-3个skill是伪需求，对10+个skill是真需求。

**解释**：
- 如果你有**2个skill**，手动维护完全OK
- 如果你有**20个skill**在生产环境跑，每天产生runtime数据，手动监控不可能
- 修身炉的价值是**规模化运维**：自动读取metrics → 检测瓶颈 → 建议优化

**当前限制**：
- V9的进化是**参数调优**（改阈值、调权重），不是**架构重写**
- 不能自动生成新的skill逻辑，只能优化现有参数
- 需要配合人工review才能安全部署

---

## Q6: 怎么写自定义skill？门槛高吗？

**门槛**：如果你会写Python函数，就能写skill。

**最小skill只需要3个文件**：
```
my-skill/
├── SKILL.md              # 说明你的技能做什么、什么时候触发
└── scripts/
    └── run.py            # 接收输入，返回JSON
```

**SKILL.md模板**（复制即用）：
```yaml
---
name: my-skill
description: 一句话说明你的技能做什么、什么时候触发。这是Agent判断是否加载你的唯一依据。
---

# 核心工作流
1. 读取输入
2. 处理逻辑
3. 输出JSON报告

## 触发条件
- 用户请求包含关键词X时自动触发
- 或：前置skill输出格式为Y时链式触发
```

**run.py模板**：
```python
import json, sys
from pathlib import Path

def main(input_path):
    data = Path(input_path).read_text()
    # ... 你的处理逻辑 ...
    report = {"result": "ok", "score": 95}
    print(json.dumps(report, ensure_ascii=False))
    return report

if __name__ == "__main__":
    main(sys.argv[1])
```

---

## Q7: 数据从哪里来？怎么接入我的Agent？

**当前模式**：文件驱动
```bash
# Agent执行任务后，把结果写入文件
python my_agent.py > result.json

# 然后手动运行skill分析
python qiti-yuanliu/scripts/entropy_scanner.py result.json
```

**建议接入模式**（未来）：
```python
# 在Agent代码中直接调用
from under-one import ContextGuard

guard = ContextGuard()
metrics = guard.scan(conversation_history)
if metrics["health_score"] < 60:
    guard.repair(conversation_history)
```

**V11目标**：提供 `pip install under-one` 的Python SDK。

---

## Q8: 为什么 metrics 是文件而不是数据库？

**设计选择**：
- 文件（JSONL）= 零依赖、零配置、可git追踪、可手动查看
- 数据库 = 需要部署、需要schema、增加运维负担

**当前适合**：个人开发者、小型团队、实验性项目

**未来扩展**：
- 如果社区需要，可以扩展出 SQLite/PostgreSQL 适配器
- 当前文件格式是标准 JSONL，任何数据库都可以导入

---

## Q9: 八卦阵的互斥矩阵是硬编码的吗？能扩展吗？

**当前**：是硬编码的（3对互斥skill）

**扩展方式**：
```python
# 在八卦阵配置中自定义互斥关系
MUTEX_PAIRS = [
    ("skill-a", "skill-b"),  # 你的自定义互斥
    ("tongtian-lu", "shenji-bailian"),  # 默认
]
```

**建议**：V11版本将互斥矩阵外部化到 `under-one.yaml`。

---

## Q10: 这个项目有实际用户在用吗？

**诚实回答**：
- 目前主要是**验证和测试阶段**
- 有完整的36场景测试 + 1200次A/B对照实验
- **尚未在真实生产环境大规模验证**

**需要社区贡献**：
- 如果你在自己的Agent项目中用了，欢迎提交 Issue 反馈效果
- 我们需要真实用户数据来优化参数

---

## 如何提交一个"好Issue"

| 类型 | 需要的信息 |
|------|-----------|
| Bug报告 | skill名称 + 输入数据 + 预期输出 + 实际输出 |
| 功能请求 | 使用场景 + 为什么现有skill不满足 |
| 性能问题 | 输入规模 + 执行时间 + 环境信息 |
| 概念质疑 | 具体哪部分映射不合理 + 你的替代建议 |

---

*维护者可以直接复制粘贴以上回答到Issue中。*
