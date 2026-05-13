---
role: agent-kernel
project: under-one
language: zh-CN
version: v0.1.0
---

# UnderOne · agent.md（元婴）

这是给 agent 看的核心入口。先读这里，再去读 README 和技能文档。

默认所有命令都从仓库根目录执行；如果需要进入 `underone/`，会在命令块里显式写出。

## 你要记住的事

- `underone/skills/*` 是源码真相，`docs/skill-cards/` 是必须保留的视觉导航。
- 每个 skill 必须保持独立、解耦、可单独安装、可单独测试、可单独验证。
- 一次只优化一个 skill；不要把全套技能一起改。
- `bagua-zhen` 的真实路径是 `underone/skills/bagua-zhen`。
- 不要把生成报告、运行产物、`runtime_data/`、`underone/reports/` 当成源码。

## 先看这些文档

1. [README.md](./README.md) - English 总览
2. [README.zh-CN.md](./README.zh-CN.md) - 中文总览
3. [docs/README.md](./docs/README.md) - 深度文档索引
4. [docs/SKILL_OPTIMIZATION_PLAYBOOK.md](./docs/SKILL_OPTIMIZATION_PLAYBOOK.md) - 单 skill 优化手册

## 标准动作

### 1) 先验证

```bash
python -m pytest -q
python underone/skills/check_versions.py
(
  cd underone
  python -m under_one.cli hosts
)
```

### 2) 再审计和验证单个 skill

```bash
(
  cd underone
  python -m under_one.cli audit priority-engine --json
  python -m under_one.cli validate-skill priority-engine --json
)
```

### 3) 再安装到指定宿主

```bash
python underone/scripts/install_host_skills.py --host codex
python underone/scripts/install_host_skills.py --host workbuddy
python underone/scripts/install_host_skills.py --host qclaw
```

隔离测试时，加 `--dest /tmp/underone-host-test`。

### 4) 再复验安装副本

```bash
python /tmp/underone-qclaw/fenghou-qimen/skillctl.py self-test
```

## Stable IDs

| Stable ID | Source Dir |
|---|---|
| `qiti-yuanliu` | `underone/skills/qiti-yuanliu` |
| `shuangquanshou` | `underone/skills/shuangquanshou` |
| `liuku-xianzei` | `underone/skills/liuku-xianzei` |
| `tongtian-lu` | `underone/skills/tongtian-lu` |
| `fenghou-qimen` | `underone/skills/fenghou-qimen` |
| `dalu-dongguan` | `underone/skills/dalu-dongguan` |
| `juling-qianjiang` | `underone/skills/juling-qianjiang` |
| `shenji-bailian` | `underone/skills/shenji-bailian` |
| `bagua-zhen` | `underone/skills/bagua-zhen` |
| `xiushen-lu` | `underone/skills/xiushen-lu` |

## 如果任务不同

- 要看怎么装和怎么复现：先读 README，再跑标准动作。
- 要逐个优化 skills：先看 `docs/SKILL_OPTIMIZATION_PLAYBOOK.md`。
- 要看全局关系和互斥：优先看 `bagua-zhen`。
- 要做造物或生成：优先看 `shenji-bailian`，但要保留测试闭环。
- 要做上下文修复：优先看 `qiti-yuanliu`，但要注意误报边界。

## 禁止项

- 不要删除插图。
- 不要修改无关的本地产物。
- 不要混淆宿主包装层和源码目录。
- 不要一次性改全套 skill。
