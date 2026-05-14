---
role: agent-kernel
project: under-one
language: zh-CN
version: v0.1.0
scope: repository-operating-contract
---

# UnderOne · agent.md（元婴）

这是给 agent 看的仓库级操作契约。先读这里，再读 README、宿主适配文档和具体 skill。

默认所有命令都从仓库根目录执行；如果需要进入 `underone/`，命令块会显式写出。平台指令、当前用户指令和安全边界永远高于本文件。

## 核心定位

UnderOne 是 10 个独立 agent skills 的工程化集合。中文名和八奇技设定是文化导航，不是运行时依赖。真正的目标是：让每个 skill 可以被单独阅读、单独安装、单独验证，并能稳定运行在 Codex、WorkBuddy、QClaw/OpenClaw 和第三方类 OpenClaw 产品中。

## 优先级

1. 当前用户目标优先于历史目标。
2. 源码和测试结果优先于 README 叙述。
3. `underone/skills/*` 是 skill 源码真相。
4. `docs/skill-cards/` 是视觉导航资产，默认必须保留。
5. 新运行产物不等于源码；不要把临时报告当作实现。

## Source Map

| Path | Meaning |
|---|---|
| `underone/skills/<skill>` | 每个 skill 的源码目录，含 `SKILL.md`、`_skillhub_meta.json`、`scripts/`、测试素材 |
| `underone/under_one/` | Python SDK、CLI、宿主适配层 |
| `underone/scripts/install_host_skills.py` | 多宿主安装入口 |
| `docs/HOST_ADAPTERS.md` | 宿主适配策略 |
| `docs/SKILL_OPTIMIZATION_PLAYBOOK.md` | 单 skill 优化循环 |
| `docs/skill-cards/` | 技能卡和总览插图 |
| `runtime_data/`、`underone/reports/` | 运行数据和临时报告，默认不当作源码修改 |

## Invariants

- 保持 10 个 skill 独立、解耦、可单独安装、可单独测试、可单独验证。
- 一次只优化一个 skill，除非用户明确要求跨 skill 架构调整。
- 修改宿主适配时必须验证 `codex`、`workbuddy`、`qclaw/openclaw`、`custom` 的语义没有互相污染。
- `bagua-zhen` 的真实路径是 `underone/skills/bagua-zhen`。
- 不删除插图，不把视觉导航降级成纯文本附录。
- 不提交无关运行产物、临时 JSON、`runtime_data/`、`underone/reports/`。

## Entry Docs

1. [README.md](./README.md) - English 总览和安装入口。
2. [README.zh-CN.md](./README.zh-CN.md) - 中文总览和安装入口。
   重点章节：第 8 节“验证配方”和第 9 节“Skill 使用样例库 / Skill example gallery”。
3. [docs/README.md](./docs/README.md) - 深度文档索引。
4. [docs/HOST_ADAPTERS.md](./docs/HOST_ADAPTERS.md) - 宿主适配策略。
5. [docs/SKILL_OPTIMIZATION_PLAYBOOK.md](./docs/SKILL_OPTIMIZATION_PLAYBOOK.md) - 单 skill 优化手册。

## 标准动作

### 1. Baseline

```bash
python -m pytest -q
python underone/skills/check_versions.py
python underone/examples/demo.py
python underone/examples/skill_showcase.py --skills context-guard priority-engine
(
  cd underone
  python -m under_one.cli hosts
  python -m under_one.cli list
)
```

### 2. One Skill Loop

```bash
(
  cd underone
  python -m under_one.cli audit priority-engine --json
  python -m under_one.cli validate-skill priority-engine --json
)
```

### 3. Host Install

```bash
python underone/scripts/install_host_skills.py --host codex
python underone/scripts/install_host_skills.py --host workbuddy
python underone/scripts/install_host_skills.py --host qclaw
python underone/scripts/install_host_skills.py --host openclaw --dest /path/to/openclaw/skills
python underone/scripts/install_host_skills.py --host custom --dest /path/to/product/skills
```

隔离验证时使用 `/tmp/...` 目录，不要直接写入真实宿主目录，除非用户明确要求。

### 4. Installed Copy Check

```bash
python underone/scripts/install_host_skills.py --host custom --dest /tmp/underone-custom --skip-source-validation fenghou-qimen
python /tmp/underone-custom/fenghou-qimen/skillctl.py self-test
```

## Host Policy

| Host | Use When | Layout | Rule |
|---|---|---|---|
| `codex` | Codex runtime | `frontmatter-wrapper` | 默认写入 `~/.codex/skills`，并生成 `agents/openai.yaml` |
| `workbuddy` | WorkBuddy runtime | `frontmatter-wrapper` | 默认写入 `~/.workbuddy/skills` |
| `qclaw` | QClaw runtime | `native-source` | 默认写入 `~/.qclaw/skills` |
| `openclaw` / `claw` | OpenClaw-like 产品 | `native-source` | 作为 `qclaw` 别名，可用 `--dest` 指向具体产品目录 |
| `custom` | 第三方产品或实验目录 | `native-source` | 必须显式传 `--dest` |

## Stable IDs

| Stable ID | Capability | Source Dir |
|---|---|---|
| `qiti-yuanliu` | 上下文漂移、自省、修复阈值 | `underone/skills/qiti-yuanliu` |
| `shuangquanshou` | 人设一致性、记忆改写边界 | `underone/skills/shuangquanshou` |
| `liuku-xianzei` | 信息消化、可信度、保鲜期 | `underone/skills/liuku-xianzei` |
| `tongtian-lu` | 任务拆解、执行计划、冲突检测 | `underone/skills/tongtian-lu` |
| `fenghou-qimen` | 优先级排序、鲁棒性评估 | `underone/skills/fenghou-qimen` |
| `dalu-dongguan` | 关联检测、异常感知、幻觉拦截 | `underone/skills/dalu-dongguan` |
| `juling-qianjiang` | 多工具/多代理调度、降级策略 | `underone/skills/juling-qianjiang` |
| `shenji-bailian` | skill/tool 生成、测试脚手架 | `underone/skills/shenji-bailian` |
| `bagua-zhen` | 生态监控、互斥仲裁、全局协调 | `underone/skills/bagua-zhen` |
| `xiushen-lu` | 自适应阈值、进化建议、回滚保护 | `underone/skills/xiushen-lu` |

## Change Protocol

修改 skill 时：

```bash
(
  cd underone
  python -m under_one.cli audit <stable-or-public-id> --json
  python -m under_one.cli validate-skill <stable-or-public-id> --json
)
python underone/scripts/install_host_skills.py --host custom --dest /tmp/underone-custom <stable-id>
python /tmp/underone-custom/<stable-id>/skillctl.py self-test
```

修改宿主适配时：

```bash
(
  cd underone
  python -m under_one.cli hosts
)
python underone/scripts/install_host_skills.py --host custom --dest /tmp/underone-custom --skip-source-validation fenghou-qimen
python underone/scripts/install_host_skills.py --host openclaw --dest /tmp/underone-openclaw --skip-source-validation fenghou-qimen
```

修改 README / docs 时：

```bash
git diff --check
python underone/skills/check_versions.py
python underone/examples/demo.py
python underone/examples/skill_showcase.py --skills context-guard priority-engine
```

## Escalation Rules

先停下来向用户确认的情况：

- 要删除或重绘 `docs/skill-cards/` 插图。
- 要改 10 个 skill 的公共协议、目录结构或版本策略。
- 要写入真实宿主目录，而不是 `/tmp/...` 隔离目录。
- 要删除大量未跟踪文件或运行产物。
- 要改变 `custom` 的默认安全策略，让它不再要求 `--dest`。

## Delivery Contract

交付前至少说明：

- 改了哪些文件和行为。
- 跑了哪些验证命令。
- 是否触碰了宿主安装目录。
- 是否还有未提交的运行产物被刻意忽略。

## 禁止项

- 不要删除插图。
- 不要混淆 public ID（如 `priority-engine`）和 stable ID（如 `fenghou-qimen`）。
- 不要把 `qclaw/openclaw/custom` 的原生布局改成 Codex frontmatter wrapper。
- 不要把临时 JSON 报告提交成源码。
- 不要一次性改全套 skill，除非用户明确要求。

## Legacy Example

如果前一步安装到了 `/tmp/underone-qclaw`：

```bash
python /tmp/underone-qclaw/fenghou-qimen/skillctl.py self-test
```
