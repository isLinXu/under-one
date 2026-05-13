#!/usr/bin/env python3
"""Tests for multi-host skill installation adapters."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from under_one.hosted_skills import (
    available_hosts,
    build_host_skill_markdown,
    default_host_skills_root,
    install_host_skill,
)


def _make_demo_skill(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "demo-skill"
    scripts_dir = skill_dir / "scripts"
    tests_dir = skill_dir / "tests"
    scripts_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)
    (skill_dir / "_skillhub_meta.json").write_text(
        json.dumps(
            {
                "id": "demo-skill",
                "name": "演示技能",
                "version": "v0.1.0",
                "entry": "scripts/run.py",
                "description": "用于演示多宿主安装适配",
                "triggers": ["演示安装", "多宿主验证"],
                "inputs": ["input.json"],
                "outputs": ["output.json"],
                "min_python": "3.8",
                "alignment": {
                    "core": "demo",
                    "agent_meaning": "demo",
                    "cost": "low",
                    "boundary": "safe",
                },
                "standalone_validation": {"kind": "python-script", "path": "tests/standalone_smoke.py"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (skill_dir / "SKILL.md").write_text(
        "---\nmetadata:\n  name: \"demo-skill\"\n  version: \"v0.1.0\"\n---\n\n# Demo\n\n## 触发词\n- 演示安装\n\n## 功能概述\ndemo\n\n## 工作流程\n1. step\n\n## 输入输出\ninput.json -> output.json\n\n## API接口\napi\n\n## 使用示例\ndemo\n\n## 测试方法\nsmoke\n",
        encoding="utf-8",
    )
    (scripts_dir / "run.py").write_text(
        "from __future__ import annotations\n\nVERSION = 'v0.1.0'\n\n\ndef main():\n    print('ok')\n\n\nif __name__ == '__main__':\n    main()\n",
        encoding="utf-8",
    )
    (tests_dir / "standalone_smoke.py").write_text(
        "from __future__ import annotations\n\n\ndef run_smoke(root, load_entry, load_meta):\n    mod = load_entry()\n    assert hasattr(mod, 'main')\n    meta = load_meta()\n    assert meta['id'] == 'demo-skill'\n    return 'demo-smoke'\n",
        encoding="utf-8",
    )
    return skill_dir


def test_available_hosts_cover_target_products():
    assert available_hosts() == ["codex", "workbuddy", "qclaw"]
    assert str(default_host_skills_root("codex")).endswith("/.codex/skills")
    assert str(default_host_skills_root("workbuddy")).endswith("/.workbuddy/skills")
    assert str(default_host_skills_root("qclaw")).endswith("/.qclaw/skills")


def test_workbuddy_markdown_uses_frontmatter_wrapper(tmp_path):
    skill_dir = _make_demo_skill(tmp_path)
    rendered = build_host_skill_markdown(skill_dir, "workbuddy")
    assert rendered.startswith("---\nname: \"demo-skill\"\ndescription:")
    assert 'host: "workbuddy"' in rendered
    assert "# Demo" in rendered


def test_qclaw_markdown_preserves_source_layout(tmp_path):
    skill_dir = _make_demo_skill(tmp_path)
    rendered = build_host_skill_markdown(skill_dir, "qclaw")
    assert rendered.startswith("---\nmetadata:\n  name: \"demo-skill\"")
    assert 'host: "qclaw"' not in rendered


def test_install_host_skill_for_workbuddy_creates_frontmatter_wrapper(tmp_path):
    skill_dir = _make_demo_skill(tmp_path)
    result = install_host_skill(skill_dir, "workbuddy", tmp_path / "workbuddy-skills", force=True)
    installed_dir = Path(result["installed_dir"])
    assert installed_dir.exists()
    assert (installed_dir / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: \"demo-skill\"")
    assert not (installed_dir / "agents" / "openai.yaml").exists()
    manifest = json.loads((installed_dir / "install-manifest.json").read_text(encoding="utf-8"))
    assert manifest["host_runtime"]["host"] == "workbuddy"
    assert result["host_validation"]["passed"] is True
    assert result["installed_lifecycle"]["passed"] is True


def test_install_host_skill_for_qclaw_keeps_native_layout(tmp_path):
    skill_dir = _make_demo_skill(tmp_path)
    result = install_host_skill(skill_dir, "qclaw", tmp_path / "qclaw-skills", force=True)
    installed_dir = Path(result["installed_dir"])
    assert installed_dir.exists()
    assert (installed_dir / "SKILL.md").read_text(encoding="utf-8").startswith("---\nmetadata:\n  name: \"demo-skill\"")
    assert not (installed_dir / "agents" / "openai.yaml").exists()
    manifest = json.loads((installed_dir / "install-manifest.json").read_text(encoding="utf-8"))
    assert manifest["host_runtime"]["host"] == "qclaw"
    assert result["host_validation"]["passed"] is True
    assert result["installed_lifecycle"]["passed"] is True
