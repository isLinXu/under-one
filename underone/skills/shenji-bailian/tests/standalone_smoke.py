from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.ToolFactory(
        {
            "artifact_type": "skill",
            "tool": {
                "name": "analysis_skill",
                "description": "分析销售数据并输出报告",
                "specialization": "analysis-skill",
            },
            "io_contract": {
                "inputs": ["records"],
                "outputs": ["report.json"],
            },
        }
    ).forge()
    assert result["artifact_type"] == "skill"
    assert result["specialization"] == "analysis-skill"
    assert any(name.endswith("/scripts/source_adapter.py") for name in result["files"])
    return f"files={len(result['files'])} specialization={result['specialization']}"
