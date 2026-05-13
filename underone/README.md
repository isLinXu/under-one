# under-one.skills

> 八奇技 · Agent 运维框架 — 让 LLM Agent 从"能跑"到"稳跑"

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**⚠️ 文化声明**: 本项目中的"八奇技"概念源自米二先生创作的漫画《一人之下》，仅作为技术社区学习交流的文化映射。所有代码与文档均为原创实现。商业使用请自行评估版权风险。

---

## 一句话介绍

under-one.skills 是一套面向 **LLM Agent 的运维技能框架**。不是提示词模板，不是工作流编排，而是解决 Agent 在真实任务中遇到的 **8个工程问题**:

| 问题 | 你的痛点 | under-one.skills 的解法 |
|------|---------|-----------------|
| 上下文乱了 | 聊了20轮，Agent忘了你说过什么 | **稳态引擎** — 自动检测矛盾并修复 |
| 多工具崩了 | 一个API挂了，整个任务链崩溃 | **调度中枢** — 降级保护，SLA监控 |
| 任务排不动 | 8件事堆在一起，不知道先干哪个 | **优先级引擎** — 九维度评分+蒙特卡洛 |
| 信息看不过来 | 50页文档，抓不住重点 | **知识消化器** — 可信度分级+保鲜期管理 |
| 人设崩了 | Agent突然换了语气/忘了原则 | **人格守护者** — DNA校验+风格锁定 |
| 想法拆不开 | "帮我做个方案"→不知道怎么拆步骤 | **指令工厂** — 自动拆解为可执行链 |
| 工具找不到 | 每次手写同样的数据处理脚本 | **工具锻造** — 需求→可运行代码 |
| 全局看不见 | 信息分散在10个文件里 | **洞察雷达** — 跨文档关联+Mermaid地图 |

---

## 30秒上手

```bash
# 1. 下载 .skill 文件
wget https://github.com/yourname/under-one-skills/releases/latest/download/under-one-skills.zip
unzip under-one-skills.zip

# 2. 安装到 Agent 技能目录
mkdir -p ~/.under-one/skills
cp *.skill ~/.under-one/skills/

# 3. 运行一个技能（独立可执行）
cd ~/.under-one/skills/fenghou-qimen/scripts
python priority_engine.py tasks.json
# → 输出: JSON {ranked_tasks, eight_gates, monte_carlo}
```

如果要安装到不同宿主：

```bash
python scripts/install_host_skills.py --host codex
python scripts/install_host_skills.py --host workbuddy
python scripts/install_host_skills.py --host qclaw
```

---

## 架构速览

```
┌─────────────────────────────────────────────┐
│              八卦阵 (中央协调器)              │
│         互斥仲裁 · 效能聚合 · 生态监控           │
└─────────────────────────────────────────────┘
        ↑                        ↑
   稳态引擎 ◄────► 指令工厂 ◄────► 洞察雷达
  (上下文守护)    (任务拆解)      (全局关联)
        ↑                        ↑
   优先级引擎 ◄────► 调度中枢 ◄────► 工具锻造
  (九维排序)      (多工具SLA)     (代码生成)
        ↑
   知识消化器 ◄────► 人格守护者
  (可信度分级)     (DNA校验)
```

---

## 10个 Skill 速查

| 英文名 | 中文名（彩蛋） | 一句话能力 | 脚本 |
|--------|-------------|-----------|------|
| `context-guard` | 炁体源流 | 自动修复上下文漂移 | `entropy_scanner.py` |
| `command-factory` | 通天箓 | 一句话拆成可执行步骤 | `fu_generator.py` |
| `insight-radar` | 大罗洞观 | 跨文档发现隐藏关联 | `link_detector.py` |
| `tool-forge` | 神机百炼 | 需求→可运行Python脚本 | `tool_factory.py` |
| `priority-engine` | 风后奇门 | 九维度任务优先级排序 | `priority_engine.py` |
| `knowledge-digest` | 六库仙贼 | 信息可信度分级+保鲜期 | `knowledge_digest.py` |
| `persona-guard` | 双全手 | DNA校验+风格漂移拦截 | `dna_validator.py` |
| `tool-orchestrator` | 拘灵遣将 | 多工具调度+降级保护 | `dispatcher.py` |
| `ecosystem-hub` | 八卦阵 | 八技状态监控+仲裁 | `coordinator.py` |
| `evolution-engine` | 修身炉 | Skill自进化+效能追踪 | `core_engine.py` |

---

## 为什么不是 LangChain / AutoGPT？

| 维度 | LangChain | AutoGPT | under-one.skills |
|------|-----------|---------|-----------|
| **定位** | 工具连接器 | 自主代理 | **代理的运维基础设施** |
| **解决的问题** | 怎么连API | 怎么让AI自己干活 | **Agent跑了之后怎么不崩** |
| **核心机制** | Chain/Tool调用链 | 循环思考-执行 | **稳态自愈+优先级+SLA监控** |
| **适用场景** | 快速搭原型 | 实验性任务 | **生产环境长任务** |

不是替代关系，是**互补**——你可以在 LangChain 应用里加载 under-one.skills skills 来提升稳定性。

---

## 项目数据

- **10** 个独立 skill
- **9** 个可执行 Python 脚本
- **44** 个剧情化测试场景
- **36/36** 场景验证通过 (100%)
- **1200** 次 A/B 对照实验
- **V10** 生产就绪版本

---

## 快速开始

### 运行单个 Skill

```bash
# 优先级排序（风后奇门）
python fenghou-qimen/scripts/priority_engine.py tasks.json

# 上下文健康扫描（炁体源流）
python qiti-yuanliu/scripts/entropy_scanner.py context.json

# 任务拆解（通天箓）
python tongtian-lu/scripts/fu_generator.py "分析竞品并生成报告"
```

### 八卦阵全局监控

```bash
python bagua-zhen/scripts/coordinator.py
# → 输出: 十技生态全景报告
```

---

## 技术细节

### 每个 Skill 的交付物

```
skill-name/
├── SKILL.md              # 技能定义 + 触发条件 + 工作流程
└── scripts/
    ├── core_script.py    # 核心执行脚本 (可直接运行)
    └── scene_*.json      # 测试场景数据
```

### 标准化接口

所有脚本遵循统一接口：
- **输入**: 文件路径或标准输入 (JSON / TXT)
- **输出**: 结构化 JSON 报告
- **Metrics**: 自动追加到 `runtime_data/{skill}_metrics.jsonl`

---

## 扩展：添加自定义 Skill

```python
# 1. 创建目录结构
mkdir my-skill/scripts

# 2. 写 SKILL.md (YAML frontmatter + Markdown body)
cat > my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: 我的自定义能力
---
# 我的技能
## 核心工作流
...
EOF

# 3. 写执行脚本
# 输入: sys.argv[1] 或 stdin
# 输出: print(json.dumps(report))
# metrics: 追加到 runtime_data/my-skill_metrics.jsonl

# 4. 打包
python package_skill.py my-skill
```

---

## 文档

| 文档 | 内容 |
|------|------|
| [完整技能详解](docs/SKILL_GUIDE.md) | 9个技能的详细机制、触发条件、输出格式 |
| [架构设计](docs/ARCHITECTURE.md) | 协同链路、互斥矩阵、八卦阵仲裁逻辑 |
| [量化验证报告](docs/QUANTIFIED_REPORT.md) | A/B对照实验、效能提升数据 |
| [世界观映射](docs/WORLDVIEW_MAPPING.md) | 《一人之下》概念到工程设计的映射说明 |
| [添加自定义Skill](docs/EXTENDING.md) | 从0到1创建skill的完整教程 |

---

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| V10 | 生产就绪、标准化、生态闭环 | ✅ |
| V11 | Python包化 (`pip install under-one`) | 📋 |
| V12 | 真实LLM集成验证 (OpenAI/Claude) | 📋 |
| V13 | 社区贡献的第三方skill市场 | 📋 |

---

## License

MIT License — 自由使用、修改、分发。请保留原始作者声明。

---

> 术之尽头，炁体源流。以身为阵，万法归一。
