#!/usr/bin/env python3
"""
real_llm_benchmark.py — 真实 LLM A/B 对照微基准

对同一批 prompt 在不同 provider 下跑一遍，对比 latency / token / 输出一致性。
适合验证适配器层工作正常、且作为后续完整 benchmark 的骨架。

使用：
    # 离线（默认 mock）
    python examples/real_llm_benchmark.py

    # 真实 OpenAI
    export OPENAI_API_KEY=sk-...
    python examples/real_llm_benchmark.py --providers mock openai

    # 真实 Anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/real_llm_benchmark.py --providers mock anthropic

    # 三家同跑
    python examples/real_llm_benchmark.py --providers mock openai anthropic
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# 允许从仓库根运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from under_one.adapters import LLMError, get_client  # noqa: E402


TEST_PROMPTS: List[Dict[str, str]] = [
    {
        "tag": "priority",
        "system": "你是任务调度助手。只用一句话回答。",
        "prompt": "给以下任务排优先级：修 P0 bug、写周报、升级依赖。",
    },
    {
        "tag": "decompose",
        "system": "你是步骤拆解助手。用 3 个 step 回答。",
        "prompt": "请把'分析竞品并生成报告'拆成可执行步骤。",
    },
    {
        "tag": "summary",
        "system": "你是摘要助手。用 20 字以内回答。",
        "prompt": "总结：今天天气晴朗，温度 22 度，风力 3 级，适合户外运动。",
    },
]


def bench_provider(provider: str, prompts: List[Dict[str, str]]) -> Dict[str, Any]:
    """在指定 provider 上跑一次全部 prompt，返回统计结果。"""
    print(f"\n=== provider = {provider} ===")
    try:
        client = get_client(provider=provider)
    except LLMError as e:
        print(f"[skipped] {e}")
        return {"provider": provider, "ok": False, "error": str(e)}

    results = []
    start_total = time.time()
    for p in prompts:
        t0 = time.time()
        try:
            resp = client.complete(
                p["prompt"], system=p["system"], max_tokens=128, temperature=0.3
            )
            elapsed_ms = (time.time() - t0) * 1000
            results.append(
                {
                    "tag": p["tag"],
                    "ok": True,
                    "latency_ms": round(elapsed_ms, 1),
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                    "preview": resp.content[:60].replace("\n", " "),
                }
            )
            print(f"  [{p['tag']:<10}] {elapsed_ms:>6.1f}ms · {resp.content[:50]}...")
        except LLMError as e:
            results.append({"tag": p["tag"], "ok": False, "error": str(e)})
            print(f"  [{p['tag']:<10}] FAILED: {e}")

    total_ms = (time.time() - start_total) * 1000
    ok_results = [r for r in results if r.get("ok")]
    summary = {
        "provider": provider,
        "model": client.model,
        "ok": bool(ok_results),
        "total_ms": round(total_ms, 1),
        "avg_latency_ms": round(
            statistics.mean(r["latency_ms"] for r in ok_results), 1
        )
        if ok_results
        else None,
        "total_prompt_tokens": sum(r.get("prompt_tokens", 0) for r in ok_results),
        "total_completion_tokens": sum(
            r.get("completion_tokens", 0) for r in ok_results
        ),
        "success_rate": f"{len(ok_results)}/{len(prompts)}",
        "results": results,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="真实 LLM A/B 对照微基准")
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["mock"],
        help="要测试的 provider 列表，默认 mock",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "artifacts" / "real_llm_benchmark.json"),
        help="结果 JSON 输出路径",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("UnderOne 真实 LLM A/B 对照微基准")
    print("=" * 60)
    print(f"测试 prompt 数: {len(TEST_PROMPTS)}")
    print(f"测试 provider: {args.providers}")

    all_results = [bench_provider(p, TEST_PROMPTS) for p in args.providers]

    # 对比表
    print("\n" + "=" * 60)
    print("对比汇总")
    print("=" * 60)
    print(f"{'provider':<12} {'model':<28} {'avg_ms':>8} {'tok_in':>7} {'tok_out':>8}")
    print("-" * 65)
    for r in all_results:
        if not r.get("ok"):
            print(f"{r['provider']:<12} SKIPPED ({r.get('error', '')})")
            continue
        print(
            f"{r['provider']:<12} {r.get('model', '')[:26]:<28} "
            f"{r.get('avg_latency_ms') or 0:>8} "
            f"{r.get('total_prompt_tokens', 0):>7} "
            f"{r.get('total_completion_tokens', 0):>8}"
        )

    # 保存
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"prompts": TEST_PROMPTS, "benchmarks": all_results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n结果已保存: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
