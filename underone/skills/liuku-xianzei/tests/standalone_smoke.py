from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.KnowledgeDigest(
        [
            {"source": "权威", "content": "核心结论：数据证明 X 有效，可用于生产部署并显著提升性能", "credibility": "S", "category": "技术方案"},
            {"source": "匿名", "content": "可能有用", "credibility": "C", "category": "默认"},
        ]
    ).digest()
    assert len(result["inheritance_queue"]) >= 1
    assert len(result["quarantine_queue"]) >= 1
    return f"avg={result['avg_digestion_rate']} inheritance={len(result['inheritance_queue'])}"
