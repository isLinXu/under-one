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
  <img src="https://img.shields.io/badge/version-V10-blue" alt="v10">
  <img src="https://img.shields.io/badge/skills-10-brightgreen" alt="10 skills">
  <img src="https://img.shields.io/badge/tests-14%2F14-success" alt="tests">
  <img src="https://img.shields.io/badge/coverage-37%25-yellow" alt="coverage">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="python">
  <img src="https://img.shields.io/badge/status-production--ready-success" alt="status">
</p>

<p align="center">
  <b>English</b> ·
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

<p align="center">
  <img src="./docs/skill-cards/00-overview-grid.png" width="640" alt="Ten Skills Grid">
</p>

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

## 7. Quickstart

```bash
# Clone and install
git clone https://github.com/isLinXu/under-one.git
cd under-one
make install                         # pip install -e underone/

under-one list                       # ten skills at a glance
under-one scan priority-engine tasks.json
under-one status                     # ecosystem snapshot
under-one providers                  # LLM adapter availability
make bundles                         # build dist/*.skill for distribution
```

**Minimal run without install:**

```bash
python underone/fenghou-qimen/scripts/priority_engine.py tasks.json
python underone/qiti-yuanliu/scripts/entropy_scanner.py context.json
python underone/bagua-zhen/scripts/coordinator.py
```

## 8. Deep example — priority-engine

Input (`tasks.json`):

```json
[
  {"id": "t1", "name": "Fix prod bug", "urgency": 5, "impact": 5, "effort": 2, "deadline_hours": 2},
  {"id": "t2", "name": "Upgrade deps", "urgency": 3, "impact": 4, "effort": 3, "deadline_hours": 48},
  {"id": "t3", "name": "Write weekly report", "urgency": 2, "impact": 2, "effort": 1, "deadline_hours": 72}
]
```

Run:

```bash
python underone/fenghou-qimen/scripts/priority_engine.py tasks.json
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

See [`underone/examples/demo.py`](./underone/examples/demo.py) for end-to-end multi-skill demos.

## 9. LLM adapter layer (v10)

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

## 10. Quantified efficacy (internal benchmark)

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

## 11. Project layout

```
under-one/
├── README.md · README.zh-CN.md   # bilingual entry docs
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
    ├── tests/                    # ── pytest suite (14 tests · 37% coverage)
    ├── examples/                 # ── demo · efficiency_benchmark · real_llm_benchmark
    ├── artifacts/                # ── sample JSON reports
    ├── scripts/                  # ── build_skill_bundles.py · tooling
    ├── under-one.yaml            #    global thresholds
    └── setup.py                  #    pip installable
```

**Why grouped under `skills/`** — the 10 skill directories are now cleanly separated from SDK / tests / examples / scripts. Picking one skill to study or package no longer needs scrolling through infrastructure folders.

## 12. Make targets

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

## 13. Roadmap

| Stage | Deliverable | Status |
|---|---|---|
| V10 | Production-ready · 10 skills · LLM adapters · CI · benchmark | ✅ Shipped |
| V11 | PyPI release · FastAPI dashboard · MCP server mode | 🚧 In progress |
| V12 | Real-LLM A/B validation report · LangChain adapter | 📋 Planned |
| V13 | Community skill marketplace · federated evolution | 💭 Vision |

## 14. FAQ (highlights)

Full answers in [`FAQ.md`](./FAQ.md):

- **Q1** Is the naming just a skin? → No. Each skill is independent; Chinese names are **cultural annotation, not functional dependency**. Rename them to `context-guard / priority-engine / …` and it works the same.
- **Q2** vs LangChain? → Complementary, not competing. See §4 above.
- **Q3** Production-ready? → V10 is used as the reference framework for the author's own agent fleets. External production usage: at your own risk.
- **Q5** Is self-evolution a fake requirement? → No — `xiushen-lu` evolves thresholds (not logic) based on runtime metrics, with rollback safeguards.
- **Q6** How to write a custom skill? → Create `my-skill/SKILL.md` + `my-skill/scripts/main.py`. ~30 lines of boilerplate, full example in docs.

## 15. Contributing

See [`CONTRIBUTING.md`](./underone/CONTRIBUTING.md). Pull requests welcome — especially for new LLM provider adapters, real-LLM benchmarks, community skills, and translation improvements.

## 16. License

MIT. Free to use, modify, distribute — please keep the original attribution.

## 17. Acknowledgement

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
