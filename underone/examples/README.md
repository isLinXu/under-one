# Examples

本目录收纳安装后即可体验的演示脚本、回归样例和基准测试。

- `demo.py` — 5 个核心 skill 的快速 smoke demo，适合首次确认包装层可用
- `skill_showcase.py` — 10 个 skill 的全量 showcase，支持 `--skills` 筛选并输出结构化 JSON 报告
- `efficiency_benchmark.py` — A/B 对照实验框架，生成量化效能报告
- `real_llm_benchmark.py` — 真实或 mock provider 的 LLM 微基准
- `forged_tools/` — **神机百炼（shenji-bailian）** 锻造出的示例工具（含 `*.py` + `*.contract.md` + `test_*.py`），可独立运行

## 推荐运行顺序

以下命令默认在仓库根目录执行，可直接复制。

```bash
# 1. 先跑最小 smoke demo
python underone/examples/demo.py

# 2. 再跑 10-skill 全量 showcase
python underone/examples/skill_showcase.py

# 3. 只验证指定 skills
python underone/examples/skill_showcase.py --skills priority-engine persona-guard

# 4. 跑基准测试
python underone/examples/efficiency_benchmark.py

# 5. 运行锻造产物
python underone/examples/forged_tools/json_cleaner.py input.json
```

`skill_showcase.py` 默认会写出 `underone/artifacts/skill_showcase.json`，并为每个 skill 分配独立沙箱目录，便于验证“独立安装、独立测试、独立输出”这条链路。
