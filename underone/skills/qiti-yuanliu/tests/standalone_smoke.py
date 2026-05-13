from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.QiTiScanner(
        [
            {"role": "user", "content": "先按 React 方案推进。", "round": 1},
            {"role": "assistant", "content": "收到，采用 React。", "round": 2},
            {"role": "user", "content": "不对，这不是这个方案，请改回之前的实现。", "round": 3},
        ]
    ).scan()
    assert result["repair_handoff"]["triggered"] is True
    assert result["self_evolution"]["rule_candidates"]
    return f"health={result['metrics']['health_score']} alerts={len(result.get('alerts', []))}"
