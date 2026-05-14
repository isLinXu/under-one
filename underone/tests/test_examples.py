#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SHOWCASE_SCRIPT = ROOT / "examples" / "skill_showcase.py"
ALL_SKILLS = [
    "context-guard",
    "command-factory",
    "insight-radar",
    "tool-forge",
    "priority-engine",
    "knowledge-digest",
    "persona-guard",
    "tool-orchestrator",
    "ecosystem-hub",
    "evolution-engine",
]


def test_skill_showcase_runs_all_wrappers_from_source_checkout(tmp_path):
    output_path = tmp_path / "skill_showcase.json"
    workspace = tmp_path / "showcase-workspace"

    result = subprocess.run(
        [
            sys.executable,
            str(SHOWCASE_SCRIPT),
            "--output",
            str(output_path),
            "--workspace",
            str(workspace),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=180,
    )

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["requested"] == 10
    assert payload["summary"]["executed"] == 10
    assert payload["summary"]["succeeded"] == 10
    assert payload["summary"]["failed"] == 0
    assert payload["selected_skills"] == ALL_SKILLS
    assert [item["id"] for item in payload["skills"]] == ALL_SKILLS
    assert all(item["success"] for item in payload["skills"])
    assert all(item["duration_ms"] >= 0 for item in payload["skills"])
    assert all("summary" in item for item in payload["skills"])
    assert (workspace / "tool-forge").exists()


def test_skill_showcase_supports_filtered_selection_and_aliases(tmp_path):
    output_path = tmp_path / "filtered_showcase.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SHOWCASE_SCRIPT),
            "--skills",
            "priority-engine",
            "shuangquanshou",
            "PriorityEngine",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=120,
    )

    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["requested"] == 2
    assert payload["summary"]["executed"] == 2
    assert payload["summary"]["failed"] == 0
    assert payload["selected_skills"] == ["priority-engine", "persona-guard"]
    assert [item["id"] for item in payload["skills"]] == ["priority-engine", "persona-guard"]
