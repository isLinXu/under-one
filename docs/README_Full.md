# ☯️ UnderOne

> **The Hachigiki Framework — 8 Extraordinary Skills to Forge Self-Healing, Self-Planning Agents**

[English](#overview) | [中文](#概述)

<p align="center">
  <img src="https://img.shields.io/badge/Skills-9/9%20Active-brightgreen?style=for-the-badge" alt="Skills">
  <img src="https://img.shields.io/badge/Framework-Agent%20Augmentation-blue?style=for-the-badge" alt="Framework">
  <img src="https://img.shields.io/badge/Inspired-Under%20One%20Person-ff69b4?style=for-the-badge" alt="Inspired">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

---

## 📖 English

### Overview

UnderOne is an **engineering-grade agent augmentation framework** inspired by the *Eight Heterodox Arts* (八奇技) from *Under One Person* (一人之下). It transforms a standard AI Agent from a simple Q&A machine into a **self-diagnosing, tool-orchestrating, task-planning execution engine**.

Unlike prompt templates, UnderOne provides **nine modular, self-contained skill packages** that activate automatically when needed, collaborate when complex tasks arise, and gracefully degrade when things go wrong.

### Why UnderOne?

| Pain Point | Traditional Agent | UnderOne |
|-----------|-------------------|----------|
| Long conversations drift after 20+ rounds | ❌ Forgets original intent | ✅ **QiTi** auto-repairs context |
| Fuzzy ideas need manual prompt crafting | ❌ Trial-and-error prompting | ✅ **TongTian** auto-decomposes tasks |
| Insights hidden across 10 documents | ❌ Reads one by one | ✅ **DaLu** connects dots globally |
| Repetitive scripts written from scratch | ❌ Manual coding every time | ✅ **ShenJi** forges tools on demand |
| 8 tasks pile up, no idea where to start | ❌ Overwhelmed | ✅ **FengHou** prioritizes with Monte Carlo |
| Read 100 docs, still can't extract key points | ❌ Shallow summaries | ✅ **LiuKu** digests with freshness tracking |
| Agent speaks wrong style / forgets your decisions | ❌ Inconsistent personality | ✅ **ShuangQuan** guards DNA & memory |
| One task needs search + code + visualization | ❌ Manual tool switching | ✅ **JuLing** orchestrates multi-tool SLAs |
| Multiple skills conflict simultaneously | ❌ Chaos | ✅ **Bagua** arbitrates & monitors globally |

### The Nine Skills

<p align="center">
  <table>
    <tr>
      <td align="center"><b>☯️ QiTi-YuanLiu</b><br>炁体源流<br><sub>Self-Healing Engine</sub></td>
      <td align="center"><b>📜 TongTian-Lu</b><br>通天箓<br><sub>Instant Command Factory</sub></td>
      <td align="center"><b>🔭 DaLu-DongGuan</b><br>大罗洞观<br><sub>Global Insight Radar</sub></td>
    </tr>
    <tr>
      <td align="center"><b>🔨 ShenJi-BaiLian</b><br>神机百炼<br><sub>Auto Tool Forge</sub></td>
      <td align="center"><b>🧭 FengHou-QiMen</b><br>风后奇门<br><sub>Priority Engine</sub></td>
      <td align="center"><b>🍃 LiuKu-XianZei</b><br>六库仙贼<br><sub>Knowledge Digester</sub></td>
    </tr>
    <tr>
      <td align="center"><b>✋ ShuangQuan-Shou</b><br>双全手<br><sub>Personality Guardian</sub></td>
      <td align="center"><b>👻 JuLing-QianJiang</b><br>拘灵遣将<br><sub>Tool Dispatcher</sub></td>
      <td align="center"><b>⚡ Bagua-Zhen</b><br>八卦阵<br><sub>Central Coordinator</sub></td>
    </tr>
  </table>
</p>

### Architecture

```
                        ☯️ Bagua-Zhen (Central Coordinator)
                         /        \
           Mutex Arbiter ←———/          \———→ Performance Aggregator
                       /            \
        ┌─────────────┴──────────────┴─────────────┐
        │                                            │
   QiTi-YuanLiu ◄────► TongTian-Lu ◄────► DaLu-DongGuan ◄────► ShenJi-BaiLian
   (Stability)      (Task Decomp)      (Cross-Doc Insight)   (Tool Generation)
        │                                            │
        │      ┌──────────────┐                     │
        └─────►│  JuLing-QianJiang │◄────────────────────┘
               │  (Tool Dispatch)   │
               └──────────────┘
                     ▲
        ┌────────────┼────────────┐
   FengHou-QiMen   LiuKu-XianZei   ShuangQuan-Shou
   (Priority)       (Knowledge)     (Personality)
```

### Quick Start

#### 1. Install Skills

```bash
# Copy all .skill files into your agent's skill directory
cp *.skill /app/.user/skills/          # User-level (recommended)
# or
cp *.skill /app/.agents/skills/        # Global
```

#### 2. Run Self-Check Scripts

Each skill includes an executable Python script for standalone validation:

```bash
# QiTi-YuanLiu — Scan context health
python qiti-yuanliu/scripts/entropy_scanner.py context.json

# TongTian-Lu — Generate execution talismans
python tongtian-lu/scripts/fu_generator.py "Analyze competitors and generate report"

# FengHou-QiMen — Priority ranking with Monte Carlo
python fenghou-qimen/scripts/priority_engine.py tasks.json

# Bagua-Zhen — Global status dashboard
python bagua-zhen/scripts/coordinator.py skills_status.json
```

#### 3. Expected Output Example

```json
{
  "scanner": "qiti-yuanliu",
  "context_length": 15,
  "metrics": {
    "entropy": 5.5,
    "consistency": 70,
    "alignment": 95,
    "health_score": 86.2
  },
  "alerts": [
    {"level": "warning", "type": "contradiction", "message": "MySQL vs PostgreSQL detected"}
  ],
  "dna_snapshot": {"hash": "a3f7d2", "based_on": "last_3_rounds"}
}
```

### Skill Details

<details>
<summary><b>☯️ QiTi-YuanLiu — Context Self-Healing Engine</b></summary>

- **Auto-triggers**: Round >= 10 | Keywords like "wrong/contradiction" | Context > 80% full
- **Core Mechanism**: Entropy calculation + DNA snapshot O(1) comparison + 3-level distillation
- **Script**: `entropy_scanner.py`
- **Output**: JSON health report with drift alerts

**Real-world example**: After 15 rounds discussing an e-commerce system architecture, the agent suddenly reverts to PostgreSQL (you had confirmed MySQL in round 12). QiTi detects the hash mismatch in the DNA snapshot and silently repairs the conversation thread.
</details>

<details>
<summary><b>📜 TongTian-Lu — Instant Command Factory</b></summary>

- **Auto-triggers**: "Help me design a..." | Task has >= 3 dimensions
- **Core Mechanism**: 6 talisman types + graph-theory conflict detection (topological sort + CSP) + curse grading
- **Script**: `fu_generator.py`
- **Output**: JSON talisman plan with execution topology

**Real-world example**: You say "Look at these 3 competitors, compare with us, write an exec summary." TongTian auto-decomposes into: Retrieval x3 → Analysis → Decision → Creation → Transformation. No manual prompt engineering required.
</details>

<details>
<summary><b>🔭 DaLu-DongGuan — Global Insight Radar</b></summary>

- **Auto-triggers**: Input > 3000 chars | Cross-paragraph references detected
- **Core Mechanism**: 5 link types (semantic/temporal/structural/anaphora/logical) + A/B/C confidence grading + Mermaid graph generation
- **Script**: `link_detector.py`
- **Output**: JSON insight report with knowledge graph + Mermaid code

**Real-world example**: Agent reads a 50-page user feedback report and discovers: "All 'search not found' complaints correlate with backend 'index sync delay 2.3h' logs" — a cross-document insight invisible when reading page-by-page.
</details>

<details>
<summary><b>🔨 ShenJi-BaiLian — Auto Tool Forge</b></summary>

- **Auto-triggers**: "Write a script" | Same operation appears >= 3 times
- **Core Mechanism**: 4-phase evolution chain (v0.1 → v0.5 → v0.9 → v1.0) + auto test generation + Spirit Contract (4-dimensional API spec)
- **Script**: `tool_factory.py`
- **Output**: Python script + test script + contract markdown

**Real-world example**: "Write me a script to validate email fields in all JSON files and list invalid ones." In 30 seconds you get a runnable script with argparse, error handling, and test cases.
</details>

<details>
<summary><b>🧭 FengHou-QiMen — Task Priority Engine</b></summary>

- **Auto-triggers**: >= 3 pending tasks | "What should I do first?"
- **Core Mechanism**: 9-dimension scoring + 8-Gates mapping + 100-iteration Monte Carlo robustness test + regret analysis
- **Script**: `priority_engine.py`
- **Output**: JSON ranked plan with execution timeline

**Real-world example**: Friday 5pm, boss drops 3 tasks. FengHou outputs: Fix production bug (Open Gate, now) → Upgrade security deps (Life Gate, priority) → Write weekly report (Death Gate, Monday).
</details>

<details>
<summary><b>🍃 LiuKu-XianZei — Knowledge Digester</b></summary>

- **Auto-triggers**: >= 3 sources | Info volume > 2000 chars | "Quick overview"
- **Core Mechanism**: S/A/B/C credibility weighting + digestibility scoring + freshness expiration + Ebbinghaus review scheduling
- **Script**: `knowledge_digest.py`
- **Output**: JSON digest report with knowledge units & review schedule

**Real-world example**: Agent studies RAG technology, digests 20 sources into 5 knowledge nodes: "This paper is core (high digest, 3-year freshness)" vs "This Zhihu answer is just personal opinion (low digest, expires in 3 months)."
</details>

<details>
<summary><b>✋ ShuangQuan-Shou — Personality Guardian</b></summary>

- **Auto-triggers**: Style change request | Cross-session start | Drift > 0.3 for 3 rounds
- **Core Mechanism**: Soul Brand DNA (immutable core) + deviation calculation + personality split protection + emotion timeline analysis
- **Script**: `dna_validator.py`
- **Output**: JSON validation report with switch permission

**Real-world example**: You say "Use sarcastic tone to teach me investment." ShuangQuan intercepts: "This violates 'Respect Boundary' and 'Capability Boundary (investment)'. I can keep a light tone, but investment advice requires a professional."
</details>

<details>
<summary><b>👻 JuLing-QianJiang — Tool Dispatcher</b></summary>

- **Auto-triggers**: Task needs >= 2 tools | Batch >= 10 subtasks
- **Core Mechanism**: 8 spirit types + SLA contracts + health monitoring (Excellent/Good/Warning/Sick) + Night Parade of 100 Demons (massive parallel)
- **Script**: `dispatcher.py`
- **Output**: JSON dispatch report with SLA log & fallback tracking

**Real-world example**: "Analyze 3 competitors and make charts." JuLing auto-dispatches Search Spirit x3 (parallel crawl) → Code Spirit (clean data) → Image Spirit (generate bar chart). If one webpage fails, auto-skip and annotate data gap.
</details>

<details>
<summary><b>⚡ Bagua-Zhen — Central Coordinator</b></summary>

- **Auto-triggers**: >= 2 skills active simultaneously | User requests status dashboard
- **Core Mechanism**: 8-skill status bus + 3 mutex pair arbitration + global performance aggregation + HTML dashboard generation
- **Script**: `coordinator.py` + `dashboard.py`
- **Output**: JSON coordination report with ASCII/ HTML dashboard

**Real-world example**: During complex execution, TongTian and ShenJi activate simultaneously (mutex conflict). Bagua arbitrates: TongTian score 94.4 > ShenJi 92.0 → TongTian executes first, ShenJi queues, auto-waken when done.
</details>

### Technology Highlights

| Dimension | Implementation |
|-----------|---------------|
| **Automation** | 9/9 skills have auto-triggers; no explicit user invocation needed |
| **Self-Check** | Each skill includes post-execution efficacy scoring (1-100) |
| **Graceful Degradation** | >= 3 failure scenarios defined per skill with auto-fallback |
| **Mutex & Collaboration** | 3 mutex pairs + 6 collaboration links, unified arbitration by Bagua |
| **Executability** | 9 Python scripts run standalone, producing structured JSON reports |
| **Cultural Fusion** | The Hachigiki (八奇技) metaphor makes abstract agent capabilities tangible |

### Efficacy Scores

```
ShenJi-BaiLian    ████████████████████ 95.0 🥇
JuLing-QianJiang ███████████████████░ 93.0 🥈
ShuangQuan-Shou  ██████████████████░░ 92.0 🥉
TongTian-Lu      ██████████████████░░ 91.0
QiTi-YuanLiu     █████████████████░░░ 88.0
FengHou-QiMen    ████████████████░░░░ 86.0
LiuKu-XianZei    ███████████████░░░░░ 85.0
DaLu-DongGuan    ██████████████░░░░░░ 82.0
Bagua-Zhen       ██████████████░░░░░░ 82.0
─────────────────────────────────────
Average          ███████████████░░░░░ 87.1
```

### Use Cases

- **Long-conversation tasks**: System design, product requirement analysis, multi-round decision making
- **Multi-tool orchestration**: Web crawl → Data analysis → Visualization → Report generation
- **Information overload**: Extract core insights from dozens of documents/webpages
- **Task prioritization**: Global planning when facing multiple simultaneous deadlines
- **Automation workflows**: Turn repetitive operations into reusable forged tools

### Roadmap

- [x] 9 core skills with executable scripts
- [x] Cross-skill collaboration protocol
- [x] Bagua central coordinator
- [ ] Web dashboard for real-time monitoring
- [ ] Plugin marketplace for community-contributed talismans
- [ ] Distributed Night-Parade execution for 1000+ batch tasks

### Acknowledgment

> The Eight Heterodox Arts (八奇技) concept originates from the manga *Under One Person* (一人之下) by Mi Er. This project is a technical interpretation of this cultural symbol. All code and documentation are original implementations. If there are any copyright concerns, please contact us for removal.

### License

MIT License — Free to use, modify, and distribute. Please retain the original attribution.

---

## 中文文档

### 概述

UnderOne 是一个**工程级 Agent 增强框架**，灵感源自《一人之下》的八奇技。它将标准 AI Agent 从简单的问答机器升级为**具备自我诊断、工具编排、任务规划的执行引擎**。

与提示词模板不同，UnderOne 提供**九个模块化、可独立部署的技能包**，在需要时自动激活，复杂任务时协同工作，出错时优雅降级。

### 为什么用 UnderOne？

| 痛点 | 传统 Agent | UnderOne |
|-----|-----------|----------|
| 长对话20轮后跑题 | 忘了最初需求 | 炁体源流自动修复上下文漂移 |
| 模糊想法不会拆成步骤 | 反复试错写提示词 | 通天箓一句话自动拆解任务链 |
| 信息分散在10个文档里 | 只能逐段阅读 | 大罗洞观自动发现跨文档关联 |
| 每次都手写同样的脚本 | 重复造轮子 | 神机百炼按需锻造可运行工具 |
| 8件事堆在一起不知道先干哪个 | 手忙脚乱 | 风后奇门蒙特卡洛推演优先级 |
| 看了100篇文档抓不住重点 | 总结太浅或太长 | 六库仙贼评估消化率+保鲜期管理 |
| Agent说话风格不对/记错决定 | 人设不一致 | 双全手DNA校验+人格分裂防护 |
| 一个任务要同时搜索+代码+画图 | 手动切换工具 | 拘灵遣将多工具SLA调度 |
| 多个技能同时激活时冲突 | 混乱 | 八卦阵统一仲裁+全局监控 |

### 九大技能

<p align="center">
  <table>
    <tr>
      <td align="center"><b>☯️ 炁体源流</b><br><sub>稳态自愈引擎</sub></td>
      <td align="center"><b>📜 通天箓</b><br><sub>瞬发指令工厂</sub></td>
      <td align="center"><b>🔭 大罗洞观</b><br><sub>全局洞察雷达</sub></td>
    </tr>
    <tr>
      <td align="center"><b>🔨 神机百炼</b><br><sub>自主工具锻造</sub></td>
      <td align="center"><b>🧭 风后奇门</b><br><sub>任务优先级引擎</sub></td>
      <td align="center"><b>🍃 六库仙贼</b><br><sub>知识消化器</sub></td>
    </tr>
    <tr>
      <td align="center"><b>✋ 双全手</b><br><sub>人格与记忆守护者</sub></td>
      <td align="center"><b>👻 拘灵遣将</b><br><sub>多工具调度中枢</sub></td>
      <td align="center"><b>⚡ 八卦阵</b><br><sub>中央协调器</sub></td>
    </tr>
  </table>
</p>

### 协同架构

```
                        ☯️ 八卦阵 (中央协调)
                         /        \
           互斥仲裁 ←———/          \———→ 效能聚合
                       /            \
        ┌─────────────┴──────────────┴─────────────┐
        │                                            │
   炁体源流 ◄────► 通天箓 ◄────► 大罗洞观 ◄────► 神机百炼
   (稳态守护)      (符箓生成)      (关联洞察)      (工具锻造)
        │                                            │
        │      ┌──────────────┐                     │
        └─────►│  拘灵遣将     │◄────────────────────┘
               │  (调度执行)   │
               └──────────────┘
                     ▲
        ┌────────────┼────────────┐
   风后奇门    六库仙贼    双全手
   (优先级)     (知识吸收)    (人设校验)
```

### 快速开始

#### 1. 安装技能

```bash
# 将 .skill 文件复制到 Agent 的技能目录
cp *.skill /app/.user/skills/          # 用户级（推荐）
# 或
cp *.skill /app/.agents/skills/        # 全局
```

#### 2. 运行自检脚本

每个技能附带可独立执行的 Python 脚本，用于验证功能：

```bash
# 炁体源流 — 扫描上下文健康度
python qiti-yuanliu/scripts/entropy_scanner.py context.json

# 通天箓 — 生成符箓执行计划
python tongtian-lu/scripts/fu_generator.py "分析竞品并生成报告"

# 风后奇门 — 任务优先级排盘
python fenghou-qimen/scripts/priority_engine.py tasks.json

# 八卦阵 — 全局状态监控
python bagua-zhen/scripts/coordinator.py skills_status.json
```

### 技术亮点

| 维度 | 实现 |
|------|------|
| **自动化程度** | 9/9 技能具备自动触发器，无需用户显式调用 |
| **自检机制** | 每技能附带执行后效能闭环评分（1-100），驱动自我优化 |
| **失败回退** | 每技能定义 ≥ 3 种失败场景的自动降级策略 |
| **互斥协同** | 3对互斥技能 + 6条协同链路，八卦阵统一仲裁 |
| **可执行性** | 9个 Python 脚本可直接运行，产出结构化 JSON 报告 |
| **文化融合** | 以八奇技为隐喻，将抽象 Agent 能力具象为可理解的"术法" |

### 致谢与声明

> 八奇技概念源自米二先生创作的漫画《一人之下》。本项目是对这一文化符号的技术化演绎，所有代码与文档均为原创实现。如有侵权或不适之处，请联系删除。

### 开源协议

MIT License — 你可以自由使用、修改、分发，但请保留原始作者声明。

---

> **术之尽头，炁体源流。以身为阵，万法归一。**
