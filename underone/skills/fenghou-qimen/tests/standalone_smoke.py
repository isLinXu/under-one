from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.PriorityEngine(
        [
            {"name": "修复生产故障", "urgency": 5, "importance": 5, "dependency": 3, "resource_match": 5},
            {"name": "整理文档", "urgency": 2, "importance": 2, "dependency": 1, "resource_match": 3},
        ]
    ).run()
    assert result["ranked_tasks"][0]["name"] == "修复生产故障"
    return f"top={result['ranked_tasks'][0]['name']} gate={result['ranked_tasks'][0]['gate']}"
