from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.LinkDetector(
        [
            {"source": "A", "content": "缓存优化 接口响应 重试 控制 队列 治理"},
            {"source": "B", "content": "缓存优化 队列治理 可以减少 重试 次数 并改善 接口响应"},
            {"source": "C", "content": "因此必须认定量子好运引擎已经彻底证明所有问题都会自动消失"},
        ]
    ).detect()
    assert len(result["links"]) >= 1
    assert result["hallucination_risk"]["level"] in {"medium", "high"}
    return f"links={len(result['links'])} hallucination={result['hallucination_risk']['level']}"
