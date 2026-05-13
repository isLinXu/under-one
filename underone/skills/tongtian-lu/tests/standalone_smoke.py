from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.FuGenerator("搜索竞品信息然后写高管报告").generate()
    assert len(result["talisman_list"]) >= 2
    assert result["dimension_count"] >= 2
    return f"talismans={len(result['talisman_list'])} curse={result['curse_level']}"
