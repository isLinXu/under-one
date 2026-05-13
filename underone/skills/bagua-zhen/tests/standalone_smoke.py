from __future__ import annotations


def run_smoke(root, load_entry, load_meta):
    import os
    import tempfile

    mod = load_entry()
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="bagua-selftest-") as tmp:
        os.chdir(tmp)
        try:
            result = mod.coordinate(skills_dir=tmp)
        finally:
            os.chdir(cwd)
    assert result["coordinator"] == "bagua-zhen"
    assert "skill_states" in result
    return f"ecosystem={result['ecosystem_level']} active={result['active_skills']}"
