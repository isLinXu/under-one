from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    import tempfile

    mod = load_entry()
    with tempfile.TemporaryDirectory(prefix="xiushen-selftest-") as tmp:
        qs = mod.QiSourceV7(tmp)
        qs.collect({"skill_name": "test", "success": True, "quality_score": 90})
        qs._flush()
        analysis = mod.RefinerV7().analyze("test", qs.load_history("test"))
    assert analysis["status"] in {"analyzed", "no_data", "stable", "warning"}
    return f"analysis_status={analysis['status']}"
