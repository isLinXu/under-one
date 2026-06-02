# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v10.3.0] - 2026-06-02

### Added - 其余五技贴合原著 + 编外身份标注（按差距从大到小）

承接 v10.2，处理批评中其余技能。所有新增能力均为**附加式**（不改既有契约、不破坏既有测试），写/改/读类动作仅做诊断或提案、不私自落盘或自动执行。

- **炁体源流 (v6.2) — 术之尽头·还炁/规则冲突消解/前置校验**（从"上下文保洁"重做为"意图还原+规则冲突消解"）
  - `distill_intent`：把任意 prompt/instruction/rules **还原为最纯粹的意图本质**——剥离修辞/客套/冗余、合并重复祈使（CLI `--reduce`）
  - `detect_rule_conflicts`：检测同主题正反冲突的"术之冲突点"并给出消解方案（CLI `--conflicts`）
  - `preflight_guard`：**众术之先的前置校验层**——他术执行前先过一遍其规则，与全局规则相冲则拦（克制他术，CLI `--preflight`）
- **大罗洞观 (v5.5) — 因果洞察+预测**（从"关联检索"重构为"穿透因果+预言"）
  - `blind_spots`：发现实体在**非相邻**片段反复浮现所暴露的认知盲区/反复纠结的症结
  - `trajectory_prediction`：据实体持续度/异常信号/因果链预测接下来若干轮的冲突/主题走向
  - `detect_parallel_dependencies`：洞察并行 agent 的隐性依赖与共享资源踩踏（CLI `--parallel`）
- **通天箓 (v6.0) — 即时画符+符箓叠加**（从"拆解"改为"即时生成+叠加"）
  - `instant_fu`：看到任务即**零 shot 即兴合成一道可直接执行(executable)的符**，可直接扔给 executor
  - `fu_stack`：诸符按可并行层**叠加组合**（而非线性 A→B→C）
- **六库仙贼 (v5.7) — 全格式吞噬+精华输出+保鲜激活**
  - `devour_any`：PDF/音视频转录/代码仓库/聊天记录/非结构化噪音皆为"食物"，归一并标注 `source_format`（CLI `--devour`）
  - `essence_units`：消化后直接吐出**可复用知识单元**（要点/出处），而非只给"消化率73%"
  - `activation_index`：消化的知识按触发词在后续对话**自动激活复现**（live / dormant），不入库吃灰
- **神机百炼 (v6.7) — 法器无主+瞬间出器**（微调）
  - `reusability`：锻出之器 `ownerless` 且 `callable_by=any-agent`，附接口契约
  - `forge_speed`：`ritual_steps=0` 零仪式即时成器

### Changed - 编外身份标注

- **八卦阵 / 修身炉** 明确标注为**编外·非八奇技**：八奇技只有八个（炁体源流/通天箓/风后奇门/神机百炼/六库仙贼/双全手/拘灵遣将/大罗洞观）。八卦阵属武侯奇门范畴；修身炉是神机百炼的造物/实例。

### Verified

- pytest 全量回归 **271 passed**（+14 新增用例；同步修正 bundle 版本快照断言 v6.1→v6.2）
- `under-one audit` 10/10 skill **0 warning / 0 error**（SKILL.md 与 `_skillhub_meta.json` 版本一致）
- CLI 冒烟：炁体 `--reduce`/`--conflicts`/`--preflight`、大罗 `--parallel`、六库 `--devour` 均 PASS

### Docs

- `docs/LORE.md`：新增「本轮增强对齐（v10.3）」五技对齐表 + 编外身份表
- 五技 `SKILL.md` 世界观补充新能力条目并同步 `_skillhub_meta.json` 版本；八卦阵/修身炉补充编外能力标注

## [v10.2.0] - 2026-06-02

### Added - 三技深度贴合原著（语义升级）

针对"拘灵/双全手/风后奇门语义偏浅"的批评，把三技从"功能近似"推进到"原著本义"。所有"写/改/覆盖"动作一律由控制面协议（问道门 `mutation_gate` + 天条 `will_not`）把关，绝不静默落盘或覆盖系统约束。

- **拘灵遣将 (v9.9) — 服灵·抽魂/聚魂/吞并**
  - `extract_soul_essence`：抽取 agent/expert 的 `soul.md` 本质（身份/系统提示摘要/能力边界/行为模式）
  - `aggregate_souls`：聚合成"魂库"（能力倒排索引 + 并集 + 魂相冲检测），附于 `dispatch` 报告的 `soul_registry`
  - `absorb_souls`：以一灵为宿主吞并其余灵能力（CLI `--absorb <host_id>`）；天条所禁与宿主禁忌冲突者拒食，吞并越多反噬风险越高
- **双全手 (v5.4) — 蓝手·改魂**
  - `parse_memory_markdown` / `render_memory_markdown`：读写 `memory.md`
  - `_build_memory_rewrite`：真正"读取→编辑→回写"记忆，报告输出 `memory_rewrite`（before/after 全文 + 操作差异 + 回滚令牌 + 门控状态）
  - `apply_memory_rewrite`：问道门把关——核心 DNA 违背→`blocked`、漂移→`review`、仅 `planned` 且 `approved=True` 才写盘并生成 `.bak` 回滚
- **风后奇门 (v5.3) — 定中宫·改局**
  - `build_domain_override` / `cast_domain`（CLI `--cast-domain`）：在声明的"领域(中宫)"内对规则/约束层生成改局提案——规则增量、阈值调整、带 TTL 自动回退的临时覆盖 + `rollback` 快照
  - 天条所禁目标拒绝；系统级/override 改局 `approval_status=pending` 必须人工审批，`applied=False`

### Verified

- pytest 全量回归 **258 passed**（+11 新增用例）
- `under-one audit` 10/10 skill **0 warning**（版本一致性同步：juling v9.9 / shuangquanshou v5.4 / fenghou v5.3）
- CLI 冒烟：风后 `--cast-domain`、拘灵 `--absorb`、双全手 `memory_rewrite` 均 PASS

### Docs

- `docs/LORE.md`：新增「本轮增强对齐（v10.2）」三技深度对齐表与安全取向说明
- 三技 `SKILL.md` 世界观补充新能力条目并同步 `_skillhub_meta.json` 版本

## [v10.1.0] - 2026-06-01

### Fixed - 设定与文档一致性

- **大罗洞观**：语录归属由"周圣"修正为"谷畸亭"（周圣实为风后奇门悟得者，属张冠李戴），同步修正 `SKILL.md`、注册表 `under_one/__init__.py`、`under-one.yaml` 三处
- **风后奇门**：统一"八门"表述——文档与代码一致实现为**七门**（开/生/休/景/惊/杜/死，"伤门"并入"杜门"），并修正示例 emoji 字典缺键（改用 `.get` 兜底）

### Added - 十技贴合度增强

- **神机百炼 (v6.6)**：异术移植 `graft_manifest` — 自动嫁接成熟基底模板/专精技法/显式 graft 请求，并标记不可用技法
- **六库仙贼 (v5.6)**：信息腐蚀（低质/污染单元量化）+ 无痕消化（高质洁净知识入库）
- **通天箓 (v5.9)**：符种细分 — 六类符箓归入漫画符种家族（侦查/攻击/防御/加速/化形…），报告输出 `species_catalog`
- **炁体源流 (v6.2)**：无限递归自省 `meta_reflect` + 炁婴自主进化轨迹
- **大罗洞观**：时间维度演化 + 命运干涉点输出
- **双全手**：性手/命手分区 + 命手积极修复方案
- **拘灵遣将**：灵契经验值积累 + 灵体弱点识别
- **修身炉**：`graft_capability` 赋能 + 与神机百炼渊源说明
- **八卦阵**：原创身份与差异化定位说明

### Verified

- pytest 全量回归 **247 passed**
- `under-one audit` 10/10 skill 结构与元数据 **0 warning**
- CLI 冒烟 **10/10 PASS**
- 新增《漫画对照分析报告》`under-one-manga-comparison-report.md`，记录修复与验证全过程

### Docs

- `docs/LORE.md`：风后奇门七门对齐表更新；新增「本轮增强对齐（v10.1）」小节与语录归属修正说明
- `README.md` / `README.zh-CN.md`：技能速查表补充新增能力关键词

## [v10.0.0] - 2025-05-03

### Added - 八奇技完整版

- **炁体源流 (qiti-yuanliu)** — 稳态自愈引擎，Agent状态实时监控与自动修复
- **通天箓 (tongtian-lu)** — 结构化指令工厂，统一Prompt生成与版本管理
- **大罗洞观 (dalu-dongguan)** — 多维洞察雷达，任务执行全过程追踪与瓶颈识别
- **神机百炼 (shenji-bailian)** — 工具锻造系统，面向任务的专用工具生成与测试
- **风后奇门 (fenghou-qimen)** — 动态优先级引擎，多任务自适应调度与资源分配
- **六库仙贼 (liuku-xianzei)** — 知识消化管道，六阶段知识吸收与结构化沉淀
- **双全手 (shuangquanshou)** — 人格守护系统，Agent行为一致性校验与价值观对齐
- **拘灵遣将 (juling-qianjiang)** — 工具调度系统，protect/possess双模式工具管理
- **八卦阵 (bagua-zhen)** — 中央协调器，八奇技互斥管理、状态聚合与协同调度
- **修身炉 (xiushen-lu)** — 自进化引擎，Agent与Skill的自动化迭代优化

### Added - 工程体系

- Python SDK (`under_one`) — 10个Skill的完整Python封装
- 统一CLI (`under-one`) — list/scan/status/evolve 四命令
- pip installable 包 (`pip install under-one-skills`)
- 全局配置文件 (`under-one.yaml`) — 阈值/关键词/策略参数
- pytest 测试套件 (7/7 通过)
- GitHub Actions CI 配置
- MIT License + 文化声明
- CONTRIBUTING.md / Issue模板 / PR模板

### Added - 量化验证

- A/B对照实验框架 (Welch's t-test + Cohen's d)
- 效率量化报告 (EFFICIENCY_QUANTIFICATION_REPORT.md)
- 基准测试脚本 (efficiency_benchmark.py)

### Added - 自进化验证

- 修身炉端到端验证通过
- Universal XiuShenLu策略模式（Code/Instruction/Hybrid）
- 五模块架构：QiSource/Refiner/Transformer/Core/Rollback
- 对任意Skill和agent.md通用

### Fixed - 世界观契合度

- 拘灵遣将："强制吞噬"改为protect(默认)/possess双模式
- 副作用系统：从惩罚机制改为纯世界观彩蛋提醒
- 六库仙贼：六阶段消化管道具象化（胃→小肠→大肠→胆→膀胱→三焦）
- 大罗洞观：增加"观测者"视角与因果追踪

## [v9.0.0] - 2025-05-02

### Changed

- V9版本全面优化：配置标准化、接口统一化
- 八卦阵中央协调器重构
- 修身炉策略模式引入

## [v8.0.0] - 2025-05-02

### Added

- 副作用世界观彩蛋系统（可选提醒）
- 拘灵遣将possess模式
- 世界观契合度审查报告

## [v7.0.0] - 2025-05-02

### Added

- 修身炉Universal模式（对任意Skill通用）
- 端到端自进化验证

## [v1.0-v6.0] - 2025-05-01

### Evolution

- V1: 基础八奇技概念映射
- V2: SKILL.md规范适配
- V3: 场景测试用例补充
- V4: 量化验证框架
- V5: 修身炉控制自进化
- V6: 世界观P0问题修复
