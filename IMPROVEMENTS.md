# UnderOne 改进路线图

> 基于 2026-05-04 项目全面审查得出的可落地改进项，按优先级 P0 / P1 / P2 分档。

---

## 已完成（本轮）

| 项目 | 状态 | 说明 |
|------|------|------|
| 清理临时产物 | ✅ | `.DS_Store` · `__pycache__/` · `.pytest_cache/` · `*.egg-info/` · `*.health_report.json` · 根目录遗留的 `test_users*.json` 与 `test_json_cleaner.py` |
| 归档散落示例 | ✅ | `underone/` 根下 13 个 demo/工具/报告文件 → `examples/forged_tools/` + `examples/demo.py` + `artifacts/` |
| 完善 `.gitignore` | ✅ | 补充 macOS / IDE / `runtime_data/` / `*.health_report.json` / `htmlcov/` 等规则 |
| 重写根 `README.md` | ✅ | 11 字节 → 完整门面（速查表 + 架构 + 快速开始 + 量化数据） |
| 新增 examples / artifacts README | ✅ | 说明两个归档目录的用途 |

## 已完成（P0 + P1 第二轮）

| 项目 | 状态 | 说明 |
|------|------|------|
| **统一版本号命名** | ✅ | `coordinator_v10/dispatcher_v9/core_engine_v7/dashboard_v7` 提升为无后缀稳定入口；老版本归档到各自 `scripts/legacy/`；CLI + SDK + SKILL.md + README 所有引用同步更新 |
| **LLM 适配层骨架** | ✅ | 新增 `under_one/adapters/`（base/mock/openai/anthropic/registry，519 行），提供统一 `LLMClient` 接口 + 自动探测逻辑，覆盖 7 个单元测试 |
| **skill 打包自动化** | ✅ | 新增 `scripts/build_skill_bundles.py`（156 行），10/10 skill 自动打包成根目录 `.skill` 文件；`make bundles` 一键构建 |
| **覆盖率与 Makefile** | ✅ | `make coverage` 生成 term + HTML 报告；当前 14 测试，adapters 70%+ 覆盖；setup.py 新增 `[openai]/[anthropic]/[llm]` 可选依赖 |

## 已完成（第三轮：根目录整理 + CLI 补全 + CI）

| 项目 | 状态 | 说明 |
|------|------|------|
| **根目录文档归档** | ✅ | 6 个 `HACHIGIKI_*.md` 历史报告 → `docs/history/`；`GITHUB_RELEASE_CHECKLIST.md` / `PROJECT_NAMING.md` → `docs/`；2 个 PNG → `docs/assets/` |
| **README 矩阵整合** | ✅ | `README_Final/Github/Hachigiki.md` 三个入口级文档迁到 `docs/`；根目录只保留一个精炼 `README.md`；新增 `docs/README.md` 索引 |
| **CLI 补全** | ✅ | `under-one bundles [--check] [skill]` + `under-one providers` 新子命令；root docstring 同步更新；`providers` 显示 API key 是否设置 |
| **CI workflow 升级** | ✅ | 矩阵更新到 3.9–3.12；加 codecov 上传；加 syntax check（跳过 legacy）；加 `bundles --check`；加 package job 自动构建 `.skill` 并作为 artifact 上传 |
| **真实 LLM benchmark 示例** | ✅ | 新增 `examples/real_llm_benchmark.py`：3 个典型 prompt × N 个 provider 对比 latency/token；支持 `--providers mock openai anthropic` 切换 |
| **mock adapter 关键词扩展** | ✅ | "拆成/步骤" 加入 decompose 触发词，benchmark 能正确命中 |

---

## P0 · 阻塞级别（建议立刻做）

### 1. 真实 LLM 集成验证（骨架已就位，剩调真实 API）
- **骨架已完成**：`under_one/adapters/{base,mock,openai,anthropic,registry}.py` 五个文件 519 行，统一 `LLMClient` 接口。
- **下一步**：
  - 填充 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY` 后写 `examples/real_llm_benchmark.py`，跑一次 A/B 产出 `REAL_LLM_VALIDATION.md`
  - 把 `examples/efficiency_benchmark.py` 接入 adapter，支持 `--provider openai` 切换

### 2. 统一版本号规范 ✅ 已完成
- 见上表。

---

## P1 · 高优先（建议近期做）

### 3. 根目录 `.skill` 文件打包自动化 ✅ 已完成
- `scripts/build_skill_bundles.py` 已实现，从 `underone/{name}/` 自动生成根目录 `{name}.skill`；`make bundles` 一键跑全量。
- **下一步**：在 GitHub Actions release 时自动执行 `make bundles` 并上传。

### 4. 命名双轨制统一
- **现状**：英文名（`context-guard`）+ 中文拼音名（`qiti-yuanliu`）并存，CLI 同时接受两套。
- **建议动作**：
  - 默认英文名作为稳定 ID，中文拼音作为彩蛋 alias
  - 文档统一使用 "context-guard (炁体源流)" 格式

### 5. 快照目录迁 git tag
- **现状**：`skill_backups/` (412K) + `skill_backups_v7/` (360K) + `skill_backups_v8/` (20K) 占据工作树。
- **建议动作**：
  ```bash
  git tag v7.0.0 <v7-commit>
  git tag v8.0.0 <v8-commit>
  git tag v9.0.0 <v9-commit>
  rm -rf skill_backups* && git commit -m "chore: remove snapshot dirs, use git tags instead"
  ```

### 6. 测试覆盖率可视化 ✅ 已完成
- `make coverage` 生成 term + `htmlcov/` HTML 报告。
- **下一步**：加 CI 徽章 + 把 coverage 上传到 codecov.io。

---

## P2 · 可选增强

### 7. pip 发布
- 路线图已列 V11，建议本周完成：
  ```bash
  python -m build
  twine upload dist/*
  ```

### 8. Web Dashboard
- 路线图 V11 规划，把八卦阵的 `dashboard.py` HTML 做成可部署的 FastAPI 服务。

### 9. Docker 镜像
- 把 SDK 打包成 `under-one/cli:v10` 镜像，方便 CI 环境使用。

### 10. 文档站
- 用 MkDocs Material 把 `README_*.md` / `*.md` 整合成 GitHub Pages 站点。

### 11. 插件市场
- V13 规划的社区第三方 skill 市场，需要先定义 skill 签名与安全沙箱规范。

### 12. 国际化
- 所有 `SKILL.md` 补充英文版 `SKILL.en.md`，面向国际开发者。

---

## 架构层面可探索

### 13. 修身炉与 ML 的结合
- 当前修身炉是基于规则的参数调优，可以接入轻量 ML（如用户当前项目 NeuroTree-Router 的思路）做自适应路由决策。

### 14. 与 LangChain / LlamaIndex 适配层
- 写 `under_one/adapters/langchain.py`，让 UnderOne skills 能作为 LangChain Tool 注入现有应用，扩大使用人群。

### 15. MCP（Model Context Protocol）Server 化
- 把每个 skill 暴露为 MCP tool，Claude Desktop 等客户端直接挂载。

---

## 清理操作记录

本轮批量清理的文件类型（可作为后续 CI 定期任务的基础）：

```bash
find . -name ".DS_Store" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -name "*.health_report.json" -delete
find . -name "*.pyc" -delete
```

建议加入到 `Makefile`：

```makefile
clean:
	find . -name ".DS_Store" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name "*.health_report.json" -delete
	find . -name "*.pyc" -delete
	@echo "✓ Clean complete"
```
