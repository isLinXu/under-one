# UnderOne 文档索引

本目录收纳项目全部深度文档。

<p align="center">
  <img src="./skill-cards/00-overview-horizontal.png" width="880" alt="UnderOne docs overview">
</p>

根目录只保留两个门面入口：
- [`README.md`](../README.md) — **English entry**
- [`README.zh-CN.md`](../README.zh-CN.md) — **中文入口**

## 视觉入口

如果你是第一次进入仓库，推荐先走这条路径：

1. 看 [`../README.md`](../README.md) 或 [`../README.zh-CN.md`](../README.zh-CN.md) 的总览插图。
2. 再到 [SKILL_OPTIMIZATION_PLAYBOOK.md](./SKILL_OPTIMIZATION_PLAYBOOK.md) 按稳定 ID 逐个优化。
3. 最后回到 `underone/skills/<skill>` 查看源码与脚本；`bagua-zhen` 也位于 `underone/skills/bagua-zhen`。

`docs/skill-cards/` 是项目的插图资产目录，建议保留；这些技能卡既服务展示，也承担文档导航作用。

## 核心文档

| 文档 | 内容 |
|------|------|
| [README_Full.md](./README_Full.md) | 早期完整中英双语项目介绍（原 `README_Final.md`，保留作归档） |
| [README_Github.md](./README_Github.md) | GitHub Release 专用说明 |
| [README_Hachigiki.md](./README_Hachigiki.md) | 八奇技世界观到工程的完整映射说明 |
| [SKILL_OPTIMIZATION_PLAYBOOK.md](./SKILL_OPTIMIZATION_PLAYBOOK.md) | 单 skill 优化手册：稳定 ID、安装路径、验证命令、推荐顺序 |
| [PROJECT_NAMING.md](./PROJECT_NAMING.md) | 项目命名设计与候选方案 |
| [GITHUB_RELEASE_CHECKLIST.md](./GITHUB_RELEASE_CHECKLIST.md) | 发布前检查清单 |

## 技能治理工作流

仓库现在内置了面向 skills 的治理门禁，默认覆盖三层：

- `make audit`：审计所有 skill 的目录结构、`_skillhub_meta.json`、`SKILL.md` 章节完整度、Mermaid 架构图、示例代码块和入口脚本埋点约定
- `make audit-report`：生成机器可读的 JSON 审计报告，落到 `underone/reports/skills-audit.json`
- `make evaluate-skills`：运行 10 个 skill 的代表性验证场景，并生成 `skill-effectiveness-report.{json,md}`
- `make check`：执行默认质量门禁，顺序为 `audit` → `test` → `bundles --check`
- `.github/workflows/skills-governance.yml`：在 `push` / `pull_request` 上运行同一套治理检查

如果只是想本地快速确认某个 skill：

```bash
cd underone
python -m under_one.cli audit fenghou-qimen --json
```

如果要验证所有分发包在当前状态下都可发布：

```bash
make check
```

如果要把审计结果喂给别的自动化流程：

```bash
make audit-report
```

如果要看每个 skill 当前的效果、运行指标和优化建议：

```bash
make evaluate-skills
```

## 多宿主安装

同一套 under-one skills 现在支持按宿主生成不同安装包装层：

- `Codex`：frontmatter wrapper + `agents/openai.yaml`
- `WorkBuddy`：frontmatter wrapper
- `QClaw`：保留原生 source layout

统一安装入口：

```bash
cd underone
python scripts/install_host_skills.py --host workbuddy
python -m under_one.cli hosts
```

## 技术文档（位于 `underone/`）

| 文档 | 内容 |
|------|------|
| [CHANGELOG](../underone/CHANGELOG.md) | 版本变更记录（V1 → V10） |
| [CONTRIBUTING](../underone/CONTRIBUTING.md) | 贡献指南 |
| [EFFICIENCY_QUANTIFICATION_REPORT](../underone/EFFICIENCY_QUANTIFICATION_REPORT.md) | A/B 对照实验完整报告 |

## 历史版本报告

`history/` 下保存各 V 版本的过程性报告，便于追溯设计演进：

- `HACHIGIKI_V6_Summary.md` / `HACHIGIKI_V7_Summary.md` — V6/V7 阶段总结
- `HACHIGIKI_36Scene_TestReport.md` — 36 个剧情化测试场景验证
- `HACHIGIKI_Quantified_Efficiency_Report_v2.md` — 量化效能早期报告
- `HACHIGIKI_WorldView_Audit_Report.md` — 世界观契合度审查
- `XiuShenLu_SelfEvolution_Verification.md` — 修身炉自进化端到端验证

## 视觉资产

- `skill-cards/` — 十大技能卡、总览栅格图、横幅图；这是当前 README 与安装导航使用的主视觉资产目录
- `assets/` — 历史 PNG 图片与演示图表

其中较常用的文件包括：

- `skill-cards/00-overview-grid.png` — 十技总览栅格图
- `skill-cards/00-overview-horizontal.png` — 横向总览图
- `hachigiki_efficiency_comparison.png` — 效能对比图
- `gdp_top10_2024.png` — 早期脚本产出的演示图表

## 根目录与此目录的分工

- **根目录** = 门面，只放入口级文档：`README.md` / `README.zh-CN.md` · `LICENSE` · `Makefile` · `FAQ.md` · `IMPROVEMENTS.md`
- **`docs/`** = 深度文档，对路过用户透明、对深度读者可达
- **`underone/`** = 工程目录，所有代码、测试、技术说明
