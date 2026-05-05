# UnderOne 文档索引

本目录收纳项目全部深度文档。

根目录只保留两个门面入口：
- [`README.md`](../README.md) — **English entry**
- [`README.zh-CN.md`](../README.zh-CN.md) — **中文入口**

## 核心文档

| 文档 | 内容 |
|------|------|
| [README_Full.md](./README_Full.md) | 早期完整中英双语项目介绍（原 `README_Final.md`，保留作归档） |
| [README_Github.md](./README_Github.md) | GitHub Release 专用说明 |
| [README_Hachigiki.md](./README_Hachigiki.md) | 八奇技世界观到工程的完整映射说明 |
| [PROJECT_NAMING.md](./PROJECT_NAMING.md) | 项目命名设计与候选方案 |
| [GITHUB_RELEASE_CHECKLIST.md](./GITHUB_RELEASE_CHECKLIST.md) | 发布前检查清单 |

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

`assets/` 下保存项目使用的 PNG 图片：

- `hachigiki_efficiency_comparison.png` — 效能对比图
- `gdp_top10_2024.png` — 早期脚本产出的演示图表

## 根目录与此目录的分工

- **根目录** = 门面，只放入口级文档：`README.md` / `README.zh-CN.md` · `LICENSE` · `Makefile` · `FAQ.md` · `IMPROVEMENTS.md`
- **`docs/`** = 深度文档，对路过用户透明、对深度读者可达
- **`underone/`** = 工程目录，所有代码、测试、技术说明
