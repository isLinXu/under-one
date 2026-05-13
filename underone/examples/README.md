# Examples

本目录收纳非核心 skill 的示例与基准测试。

- `demo.py` — 端到端演示脚本（展示多 skill 协同调用）
- `efficiency_benchmark.py` — A/B 对照实验框架，生成量化效能报告
- `forged_tools/` — **神机百炼（shenji-bailian）** 锻造出的示例工具（含 `*.py` + `*.contract.md` + `test_*.py`），可独立运行

## 运行示例

以下命令默认在 `underone/` 目录执行。

```bash
# 端到端演示
python examples/demo.py

# 跑基准测试
python examples/efficiency_benchmark.py

# 运行锻造产物
python examples/forged_tools/json_cleaner.py input.json
```
