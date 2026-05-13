from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.dispatch(
        [{"type": "code", "desc": "查询资料"}],
        [
            {"id": "api1", "capabilities": ["code"], "available": False, "quality_score": 0.95},
            {"id": "api2", "capabilities": ["browse"], "available": True, "quality_score": 0.90},
        ],
        strategy="protect",
    )
    assert result["fallback_count"] >= 1
    assert len(result["plan"]) == 1
    return f"fallbacks={result['fallback_count']} quality={result['avg_quality']}"
