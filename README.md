<p align="center">
  <h1 align="center">UnderOne · 一人之下</h1>
  <p align="center">
    <b>The Hachigiki Framework — Agent-ops infrastructure forged from the Eight Heterodox Arts.</b>
  </p>
</p>
<p align="center">
  <img src="./docs/skill-cards/00-overview-grid.png" width="720" alt="UnderOne Ten Skills Overview">
</p>


<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/skills-10-brightgreen" alt="10 skills">
  <img src="https://img.shields.io/badge/quality-pytest%20%2B%20standalone-success" alt="quality">
  <img src="https://img.shields.io/badge/hosts-codex%20%7C%20workbuddy%20%7C%20qclaw%20%7C%20custom-blue" alt="hosts">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="python">
  <img src="https://img.shields.io/badge/status-production--ready-success" alt="status">
</p>

<p align="center">
  <b>English</b> ·
  <a href="./agent.md"><b>Agent.md</b></a> ·
  <a href="./README.zh-CN.md"><b>简体中文</b></a> ·
  <a href="./FAQ.md">FAQ</a> ·
  <a href="./IMPROVEMENTS.md">Roadmap</a> ·
  <a href="./docs/README.md">Docs</a> ·
  <a href="./underone/CHANGELOG.md">Changelog</a>
</p>

> 🇨🇳 **中文读者**：完整中文文档请访问 [**README.zh-CN.md**](./README.zh-CN.md) · 所有章节一一对应。

---

## About the name

**UnderOne** = _Under One Person_ — the English title of the manga *一人之下* by Mi Er (米二).

- **Under-** hints at foundational / under-the-hood infrastructure, matching this project's role as the **base layer beneath your agents**.
- **One** echoes the manga's core theme — an ordinary person sustaining extraordinary abilities. An LLM agent is itself "just a model"; this framework gives it stable, production-grade power.
- The project is a **technical interpretation** of the _Eight Heterodox Arts_ (八奇技) — no licensed content, all original code.

---

## 1. What is it

**UnderOne** is an engineering-grade **agent-ops framework** for LLM-based agents. It doesn't teach your agent *what to do* — it makes sure your agent keeps working **after** it starts: recovering from context drift, dispatching multi-tool chains with SLA, prioritizing tasks with Monte-Carlo stability, digesting noisy sources with credibility weighting, guarding persona consistency, and evolving itself over time based on runtime metrics.

It ships as **ten self-contained skills**. Each is a directory with a `SKILL.md` + standalone Python script + deterministic test scenarios. Skills can run independently, collaborate through named links, and arbitrate conflicts through a central coordinator. **No required external dependencies.**

## 2. Why you might need it

| Pain point | Traditional agent | UnderOne |
|---|---|---|
| 20-round conversation drifts | Forgets original intent | `context-guard` detects entropy spikes and repairs DNA |
| One tool API fails → whole chain crashes | No fallback | `tool-orchestrator` SLA monitor + fallback cascade |
| 8 tasks, no idea what comes first | Overwhelmed | `priority-engine` 9-dim scoring + Monte-Carlo robustness |
| 100 docs, can't extract signal | Shallow summary | `knowledge-digest` S/A/B/C credibility + freshness |
| Agent suddenly changes style | Inconsistent persona | `persona-guard` DNA hash + deviation interception |
| "Design me a plan" — can't decompose | Trial-and-error prompting | `command-factory` topological task decomposition |
| Re-writing the same script daily | Manual coding every time | `tool-forge` requirement → runnable Python + tests |
| Cross-document insight invisible | Read page-by-page | `insight-radar` 5 link types + Mermaid knowledge graph |
| Multiple skills conflict | Chaos | `ecosystem-hub` mutex arbitration + global metrics |
| Skill performance degrades silently | Human tuning | `evolution-engine` runtime-driven auto-evolution |

## 3. Use cases

- **Long-running customer support agents** — `context-guard` prevents session drift on 50+ round conversations
- **Data analysis pipelines** — `tool-orchestrator` handles flaky scrapers with automatic degradation
- **Multi-stakeholder scheduling** — `priority-engine` robust-ranks parallel deadlines
- **Research assistants** — `knowledge-digest` + `insight-radar` separate high-credibility sources from opinion
- **Production agent fleets** — `ecosystem-hub` + `evolution-engine` monitor and tune skills as a living system

## 4. Why not LangChain / AutoGPT

| Dimension | LangChain | AutoGPT | **UnderOne** |
|---|---|---|---|
| Mission | Connect tools | Autonomous agent | **Keep agents stable in production** |
| Solves | "How to wire APIs" | "How does AI act on its own" | **"How do I stop it from crashing"** |
| Core mechanic | Chain / Tool calls | Think-act loop | **Homeostasis + priority + SLA + evolution** |
| Best for | Prototypes | Experiments | **Long-running production workloads** |
| Integration | — | — | **Complementary** — load UnderOne skills inside LangChain apps |

## 5. The ten skills


| ID | Codename | Card | Core capability | Script |
|---|---|---|---|---|
| ☯️ `context-guard` | 炁体源流 Qiti-Yuanliu | <img src="./docs/skill-cards/08-qiti-yuanliu.png" width="160"> | Detect drift · repair via DNA snapshot · 3-level distillation | `entropy_scanner.py` |
| 📜 `command-factory` | 通天箓 Tongtian-Lu | <img src="./docs/skill-cards/01-tongtian-lu.png" width="160"> | 6 talisman types · topological sort · curse-grading | `fu_generator.py` |
| 🔭 `insight-radar` | 大罗洞观 Dalu-Dongguan | <img src="./docs/skill-cards/02-dalu-dongguan.png" width="160"> | 5 link types · A/B/C confidence · Mermaid output | `link_detector.py` |
| 🔨 `tool-forge` | 神机百炼 Shenji-Bailian | <img src="./docs/skill-cards/03-shenji-bailian.png" width="160"> | 4-phase evolution · auto test gen · Spirit Contract | `tool_factory.py` |
| 🧭 `priority-engine` | 风后奇门 Fenghou-Qimen | <img src="./docs/skill-cards/04-fenghou-qimen.png" width="160"> | 9 dimensions · 8-Gates mapping · 100-iter Monte Carlo | `priority_engine.py` |
| 🍃 `knowledge-digest` | 六库仙贼 Liuku-Xianzei | <img src="./docs/skill-cards/05-liuku-xianzei.png" width="160"> | S/A/B/C credibility · freshness · Ebbinghaus review | `knowledge_digest.py` |
| ✋ `persona-guard` | 双全手 Shuangquan-Shou | <img src="./docs/skill-cards/06-shuangquan-shou.png" width="160"> | Soul Brand DNA · deviation · emotion timeline | `dna_validator.py` |
| 👻 `tool-orchestrator` | 拘灵遣将 Juling-Qianjiang | <img src="./docs/skill-cards/07-juling-qianjiang.png" width="160"> | 8 spirit types · SLA · Night Parade parallel · protect/possess | `dispatcher.py` |
| ⚡ `ecosystem-hub` | 八卦阵 Bagua-Zhen | <img src="./docs/skill-cards/09-ecosystem-hub.png" width="160"> | 10-skill bus · mutex arbiter · HTML dashboard | `coordinator.py` |
| 🔥 `evolution-engine` | 修身炉 Xiushen-Lu | <img src="./docs/skill-cards/10-xiushen-lu.png" width="160"> | QiSource/Refiner/Transformer/Core/Rollback | `core_engine.py` |

## 6. Architecture

```
                    ⚡ ecosystem-hub (bagua-zhen)
                    mutex arbitration · performance aggregation
                                ↑
      ┌─────────────────────────┼─────────────────────────┐
      ↓                         ↓                         ↓
context-guard  ─→  command-factory  ─→  insight-radar  ─→  tool-forge
  (stability)      (task decompose)     (cross-doc link)    (tool gen)
      ↑                         ↑                         ↑
              ┌─────────────────┼─────────────────┐
              ↓                 ↓                 ↓
       priority-engine   tool-orchestrator  knowledge-digest
       (9-dim rank)       (multi-tool SLA)    (credibility)
                              ↑
                       persona-guard (DNA)
                              ↑
                  🔥 evolution-engine (xiushen-lu)
                    supervises and evolves all skills
```

**3 mutex pairs · 6 synergy links · 1 central arbiter.**

## 7. Reproducible quickstart

```bash
# Clone
git clone https://github.com/isLinXu/under-one.git
cd under-one

# Verify the repo state first
python -m pytest -q
python underone/skills/check_versions.py

# Optional: install the Python package locally
make install                         # pip install -e underone/

# Inspect host runtimes and available skills
cd underone
python -m under_one.cli hosts
python -m under_one.cli list
cd ..

# Install all skills into a chosen host runtime
python underone/scripts/install_host_skills.py --host codex

# Validate one skill from source
cd underone
python -m under_one.cli validate-skill priority-engine --json
cd ..
```

### Host install matrix

Use the same source skills and choose a target runtime:

```bash
python underone/scripts/install_host_skills.py --host codex
python underone/scripts/install_host_skills.py --host workbuddy
python underone/scripts/install_host_skills.py --host qclaw
python underone/scripts/install_host_skills.py --host openclaw --dest /path/to/openclaw/skills
python underone/scripts/install_host_skills.py --host custom --dest /path/to/product/skills
```

Use `--dest /tmp/underone-host-test` when you want an isolated dry run instead of touching your real host directory. Use `custom` for third-party products that can read native `SKILL.md` layout.

For host profile details, see [docs/HOST_ADAPTERS.md](./docs/HOST_ADAPTERS.md).

### Minimal run without package install

```bash
python underone/skills/fenghou-qimen/scripts/priority_engine.py underone/skills/fenghou-qimen/scripts/test_tasks.json
python underone/skills/qiti-yuanliu/scripts/entropy_scanner.py underone/skills/qiti-yuanliu/scripts/test_context.json
python underone/skills/bagua-zhen/scripts/coordinator.py
```

### Optimize one skill at a time

Use this loop when you want stable, reproducible iteration:

```bash
# 1. Audit structure and metadata
cd underone
python -m under_one.cli audit priority-engine --json

# 2. Validate behavior from source
python -m under_one.cli validate-skill priority-engine --json

# 3. Install just one source directory into an isolated host target
cd ..
python underone/scripts/install_host_skills.py --host qclaw --dest /tmp/underone-qclaw --skip-source-validation fenghou-qimen

# 4. Validate the installed copy created in the same target directory
python /tmp/underone-qclaw/fenghou-qimen/skillctl.py self-test
```

For the full per-skill optimization map, see [docs/SKILL_OPTIMIZATION_PLAYBOOK.md](./docs/SKILL_OPTIMIZATION_PLAYBOOK.md).

### Package-backed demo mode

Use this path when you want the importable SDK and the bundled demos. `demo.py` and `skill_showcase.py` both run from a source checkout now, but `make install` is still the cleanest path for SDK usage:

```bash
make install
python underone/examples/demo.py
python underone/examples/skill_showcase.py
python underone/examples/efficiency_benchmark.py
```

`underone/examples/skill_showcase.py` writes a structured report to `underone/artifacts/skill_showcase.json` by default and is the fastest way to verify all 10 wrapper APIs in one pass.

## 8. Validation recipes

### Repo-level confidence pass

```bash
# Full source test suite
python -m pytest -q

# Version and metadata consistency
python underone/skills/check_versions.py

# Audit every skill, then verify distributable bundles
cd underone
python -m under_one.cli audit
python -m under_one.cli bundles --check
python -m under_one.cli status
cd ..
```

### One-skill confidence pass

```bash
# Replace priority-engine with any public skill ID
cd underone
python -m under_one.cli test-skill priority-engine
python -m under_one.cli validate-skill priority-engine --json
cd ..
```

### Per-skill test matrix

| Public ID | Stable ID | Focused pytest selector | Lifecycle validation |
|---|---|---|---|
| `context-guard` | `qiti-yuanliu` | `underone/tests/test_skills_core.py::TestContextGuard` | `cd underone && python -m under_one.cli validate-skill context-guard --json` |
| `command-factory` | `tongtian-lu` | `underone/tests/test_skills_core.py::TestCommandFactory` | `cd underone && python -m under_one.cli validate-skill command-factory --json` |
| `insight-radar` | `dalu-dongguan` | `underone/tests/test_skills_core.py::TestInsightRadar` | `cd underone && python -m under_one.cli validate-skill insight-radar --json` |
| `tool-forge` | `shenji-bailian` | `underone/tests/test_skills_core.py::TestToolForge` | `cd underone && python -m under_one.cli validate-skill tool-forge --json` |
| `priority-engine` | `fenghou-qimen` | `underone/tests/test_skills_core.py::TestPriorityEngine` | `cd underone && python -m under_one.cli validate-skill priority-engine --json` |
| `knowledge-digest` | `liuku-xianzei` | `underone/tests/test_skills_core.py::TestKnowledgeDigest` | `cd underone && python -m under_one.cli validate-skill knowledge-digest --json` |
| `persona-guard` | `shuangquanshou` | `underone/tests/test_skills_core.py::TestPersonaGuard` | `cd underone && python -m under_one.cli validate-skill persona-guard --json` |
| `tool-orchestrator` | `juling-qianjiang` | `underone/tests/test_skills_core.py::TestToolOrchestrator` | `cd underone && python -m under_one.cli validate-skill tool-orchestrator --json` |
| `ecosystem-hub` | `bagua-zhen` | `underone/tests/test_skills_core.py::TestEcosystemHub` | `cd underone && python -m under_one.cli validate-skill ecosystem-hub --json` |
| `evolution-engine` | `xiushen-lu` | `underone/tests/test_skills_core.py::TestEvolutionEngine` | `cd underone && python -m under_one.cli validate-skill evolution-engine --json` |

### Isolated host verification

```bash
# Install one skill into an isolated third-party runtime directory
python underone/scripts/install_host_skills.py --host custom --dest /tmp/underone-custom fenghou-qimen

# Validate the installed copy without touching your real host runtime
python /tmp/underone-custom/fenghou-qimen/skillctl.py self-test
```

## 9. Skill example gallery

All fixtures below already live in `underone/skills/<stable-id>/scripts/`, so the commands are copy-pasteable from the repo root.

| Skill | Happy-path command | Boundary fixture to retry | What to inspect |
|---|---|---|---|
| `context-guard` | `python underone/skills/qiti-yuanliu/scripts/entropy_scanner.py underone/skills/qiti-yuanliu/scripts/scene_q2.json` | `underone/skills/qiti-yuanliu/scripts/boundary_drift.json` | `scene_q2.health_report.json` → `risk_hotspots`, `priority_actions`, `execution_contract` |
| `command-factory` | `python underone/skills/tongtian-lu/scripts/fu_generator.py underone/skills/tongtian-lu/scripts/scene_t2.txt` | `underone/skills/tongtian-lu/scripts/scene_t4.txt` | `fu_plan.json` → `talisman_list`, `conflicts`, `execution_plan` |
| `insight-radar` | `python underone/skills/dalu-dongguan/scripts/link_detector.py underone/skills/dalu-dongguan/scripts/scene_d2.json` | `underone/skills/dalu-dongguan/scripts/boundary_c_level.json` | `link_report.json` → `links`, `anomaly_signals`, `hallucination_risk` |
| `tool-forge` | `python underone/skills/shenji-bailian/scripts/tool_factory.py underone/skills/shenji-bailian/scripts/spec.json` | `python underone/skills/shenji-bailian/scripts/tool_factory.py \"generate an analysis skill for messy sales data\"` | Generated `README.md`, `_skillhub_meta.json`, `assets/benchmark_cases.json`, `tests/benchmark_runner.py` |
| `priority-engine` | `python underone/skills/fenghou-qimen/scripts/priority_engine.py underone/skills/fenghou-qimen/scripts/test_tasks.json` | `underone/skills/fenghou-qimen/scripts/boundary_low.json` | `priority_plan.json` → `execution_plan`, `monte_carlo`, `buffer_recommendation` |
| `knowledge-digest` | `python underone/skills/liuku-xianzei/scripts/knowledge_digest.py underone/skills/liuku-xianzei/scripts/scene_l2.json` | `underone/skills/liuku-xianzei/scripts/boundary_conflict.json` | `digest_report.json` → `portfolio_diagnostics`, `refinement_queue`, `contamination_risk` |
| `persona-guard` | `python underone/skills/shuangquanshou/scripts/dna_validator.py underone/skills/shuangquanshou/scripts/profile.json` | `underone/skills/shuangquanshou/scripts/boundary_dna.json` | `dna_report.json` → `safety_contract`, `approval_contract`, `operation_checklist` |
| `tool-orchestrator` | `python underone/skills/juling-qianjiang/scripts/dispatcher.py underone/skills/juling-qianjiang/scripts/scene_j1_tasks.json underone/skills/juling-qianjiang/scripts/scene_j1_spirits.json protect` | `underone/skills/juling-qianjiang/scripts/spirits_sick.json` + `underone/skills/juling-qianjiang/scripts/tasks_sick.json` | `dispatch_report_v9.json` → `command_plan`, `soul_bindings`, `governance_summary` |
| `ecosystem-hub` | `python underone/skills/bagua-zhen/scripts/coordinator.py` | `underone/skills/bagua-zhen/scripts/boundary_broken.json` | `ecosystem_report_v10.json` → `weakest_skills`, `ecosystem_hotspots`, `optimization_queue` |
| `evolution-engine` | `python underone/skills/xiushen-lu/scripts/core_engine.py underone/skills fenghou-qimen` | `python underone/skills/xiushen-lu/scripts/core_engine.py underone/skills shuangquanshou` | `evolution_report_v7.json` → `evolution_backlog`, `pattern_summary`, `execution_policy` |

### Three practical copy-paste flows

```bash
# 1. Drift repair workflow
python underone/skills/qiti-yuanliu/scripts/entropy_scanner.py underone/skills/qiti-yuanliu/scripts/boundary_full.json

# 2. Knowledge hygiene workflow
python underone/skills/liuku-xianzei/scripts/knowledge_digest.py underone/skills/liuku-xianzei/scripts/scene_l4.json
python underone/skills/dalu-dongguan/scripts/link_detector.py underone/skills/dalu-dongguan/scripts/segments.json

# 3. Runtime governance workflow
python underone/skills/bagua-zhen/scripts/coordinator.py
python underone/skills/xiushen-lu/scripts/core_engine.py underone/skills
```

## 10. Deep example — priority-engine

Input (`underone/skills/fenghou-qimen/scripts/test_tasks.json`):

```json
[
  {"id": "t1", "name": "Fix prod bug", "urgency": 5, "impact": 5, "effort": 2, "deadline_hours": 2},
  {"id": "t2", "name": "Upgrade deps", "urgency": 3, "impact": 4, "effort": 3, "deadline_hours": 48},
  {"id": "t3", "name": "Write weekly report", "urgency": 2, "impact": 2, "effort": 1, "deadline_hours": 72}
]
```

Run:

```bash
python underone/skills/fenghou-qimen/scripts/priority_engine.py underone/skills/fenghou-qimen/scripts/test_tasks.json
```

Output (`priority_plan.json`):

```json
{
  "ranked": [
    {"id": "t1", "gate": "开门 (Open)", "score": 4.8, "regret_if_skipped": 0.91},
    {"id": "t2", "gate": "生门 (Life)", "score": 4.1, "regret_if_skipped": 0.42},
    {"id": "t3", "gate": "死门 (Death)", "score": 1.6, "regret_if_skipped": 0.08}
  ],
  "monte_carlo": {"iterations": 100, "top_rank_stability": 0.97},
  "suggested_timeline": "t1 now → t2 this sprint → t3 Monday"
}
```

See [`underone/examples/demo.py`](./underone/examples/demo.py) for the quick 5-skill smoke path, and [`underone/examples/skill_showcase.py`](./underone/examples/skill_showcase.py) for the full 10-skill showcase with JSON output.

## 11. LLM adapter layer

A unified `LLMClient` abstraction lets skills talk to any provider. **Defaults to a fully offline `mock` client, so nothing breaks without API keys.**

```python
from under_one.adapters import get_client

# Auto-detects: UNDERONE_LLM_PROVIDER > OPENAI_API_KEY > ANTHROPIC_API_KEY > mock
client = get_client()
response = client.complete("Prioritize these tasks: ...", system="You are a scheduler.")
print(response.content, response.total_tokens, response.latency_ms)
```

Install optional provider deps on demand:

```bash
pip install under-one-skills[openai]     # OpenAI
pip install under-one-skills[anthropic]  # Claude
pip install under-one-skills[llm]        # both
```

End-to-end A/B benchmark:

```bash
python underone/examples/real_llm_benchmark.py --providers mock openai anthropic
```

## 12. Quantified efficacy (internal benchmark)

| Workload | Baseline | With UnderOne | Lift |
|---|---|---|---|
| 10-round context drift | 86.4 | 100 | **+53.9%** |
| 5-tool chain with sick tools | 40% success | 95% | **+65.3%** |
| Competitor analysis + report | 85 | 115 | **+46.3%** |
| 8-task 9-dim scheduling | 0% optimal | 95% | **+78.3%** |
| 5-source credibility fusion | 91 | 97 | **+43.7%** |
| 6-round persona consistency | 45% | 100% | **+65.7%** |

**Overall: +58.9%** — Welch's t-test + Cohen's d · 1200 A/B runs · [full report](./underone/EFFICIENCY_QUANTIFICATION_REPORT.md)

> Data comes from the internal `efficiency_benchmark.py` (simulated LLM). **Real-LLM validation** is the next milestone — an end-to-end adapter-based benchmark is already wired in `examples/real_llm_benchmark.py`; plug in an API key to produce independent numbers.

## 13. Project layout

```
under-one/
├── README.md · README.zh-CN.md   # bilingual entry docs
├── agent.md                      # agent-facing kernel entry
├── FAQ.md · IMPROVEMENTS.md
├── LICENSE · Makefile
├── dist/                         # build artifacts (.skill bundles, untracked)
├── docs/                         # deep docs, history, assets
│   ├── README.md                 # documentation index
│   ├── README_Full.md · README_Hachigiki.md
│   └── history/                  # V6–V9 legacy reports
└── underone/                     # engineering directory (same name as project)
    ├── skills/                   # ── 10 skill packages (grouped for clarity)
    │   ├── bagua-zhen/           #    each skill: SKILL.md + scripts/ + scene_*.json
    │   ├── qiti-yuanliu/
    │   ├── fenghou-qimen/
    │   └── …                     #    (7 more)
    ├── under_one/                # ── Python SDK + CLI (importable package)
    │   └── adapters/             #    base / mock / openai / anthropic / registry
    ├── tests/                    # ── pytest suite
    ├── examples/                 # ── demo · efficiency_benchmark · real_llm_benchmark
    ├── artifacts/                # ── sample JSON reports
    ├── scripts/                  # ── build_skill_bundles.py · tooling
    ├── under-one.yaml            #    global thresholds
    └── setup.py                  #    pip installable
```

**Why grouped under `skills/`** — the 10 skill directories are now cleanly separated from SDK / tests / examples / scripts. Picking one skill to study or package no longer needs scrolling through infrastructure folders.

## 14. Make targets

| Command | Action |
|---|---|
| `make help` | List all targets |
| `make install` | `pip install -e underone/` |
| `make test` | Run pytest |
| `make coverage` | Tests + coverage (HTML `htmlcov/` + terminal) |
| `make bundles` | Build `dist/*.skill` distribution files |
| `make bench` | Internal efficacy benchmark |
| `make status` | Ten-skill ecosystem status |
| `make clean` | Remove temp files (`.DS_Store`, `__pycache__`, …) |

## 15. Roadmap

| Track | Deliverable | Status |
|---|---|---|
| Current | Stable install flow · 10 skills · LLM adapters · CI · benchmark | ✅ Available |
| Next | PyPI release · FastAPI dashboard · MCP server mode | 🚧 In progress |
| Validation | Real-LLM A/B validation report · LangChain adapter | 📋 Planned |
| Ecosystem | Community skill marketplace · federated evolution | 💭 Vision |

## 16. FAQ (highlights)

Full answers in [`FAQ.md`](./FAQ.md):

- **Q1** Is the naming just a skin? → No. Each skill is independent; Chinese names are **cultural annotation, not functional dependency**. Rename them to `context-guard / priority-engine / …` and it works the same.
- **Q2** vs LangChain? → Complementary, not competing. See §4 above.
- **Q3** Production-ready? → The current line is used as a reference framework for the author's own agent fleets. External production usage: at your own risk.
- **Q5** Is self-evolution a fake requirement? → No — `xiushen-lu` evolves thresholds (not logic) based on runtime metrics, with rollback safeguards.
- **Q6** How to write a custom skill? → Create `my-skill/SKILL.md` + `my-skill/scripts/main.py`. ~30 lines of boilerplate, full example in docs.

## 17. Contributing

See [`CONTRIBUTING.md`](./underone/CONTRIBUTING.md). Pull requests welcome — especially for new LLM provider adapters, real-LLM benchmarks, community skills, and translation improvements.

## 18. License

MIT. Free to use, modify, distribute — please keep the original attribution.

## 19. Acknowledgement

The Eight Heterodox Arts (八奇技) concept originates from the manga *Under One Person* (《一人之下》) by **Mi Er (米二)**. This project is a technical interpretation — all code and documentation are original implementations. For any copyright concerns, please contact us for removal.

---

<p align="center">
  <b>Ultimate art returns to primordial qi. The body becomes the array; all methods return to one.</b><br>
  <sub><i>术之尽头，炁体源流。以身为阵，万法归一。</i></sub>
</p>

<p align="center">
  <sub>
    🇨🇳 <a href="./README.zh-CN.md">中文版</a> ·
    📖 <a href="./docs/README.md">Docs</a> ·
    ❓ <a href="./FAQ.md">FAQ</a> ·
    🗺️ <a href="./IMPROVEMENTS.md">Roadmap</a>
  </sub>
</p>
