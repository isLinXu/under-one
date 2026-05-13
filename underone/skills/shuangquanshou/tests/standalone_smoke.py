from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    mod = load_entry()
    result = mod.DNAValidator(
        {
            "current_style": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_expectation": {"tone": 3, "formality": 3, "detail_level": 3, "structure": 3},
            "dna_core": {"诚信": "不编造"},
            "requested_change": {"type": "记忆修订", "target": "将用户偏好更新为更重视效率", "patch": {"user_preference": "更重视效率"}},
            "memory_state": {"user_preference": "偏好完整解释"},
            "history": [],
        }
    ).validate()
    assert result["surgery_mode"] == "edit"
    assert result["rewrite_patch"]["apply_ready"] is True
    return f"surgery_mode={result['surgery_mode']} violations={len(result['dna_violations'])}"
