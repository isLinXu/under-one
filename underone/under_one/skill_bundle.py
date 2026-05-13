"""Helpers for parsing and installing standalone `.skill` bundles."""

from __future__ import annotations

import json
import re
import subprocess
import shutil
import textwrap
import tempfile
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


BUNDLE_HEADER = "===== UNDER-ONE SKILL BUNDLE v1 ====="
BUNDLE_FOOTER = "===== END BUNDLE ====="
FILE_PREFIX = "----- file: "
FILE_SUFFIX = " -----"
EXCLUDE_DIRS = {"legacy", "__pycache__", "runtime_data", "backups"}
EXCLUDE_SUFFIXES = {".pyc", ".health_report.json"}
SHARED_PREFIX = "__shared__/"
SHARED_HELPER_MODULES = {
    "metrics_collector": "metrics_collector.py",
    "_skill_config": "_skill_config.py",
    "skill_base": "skill_base.py",
}


SKILLCTL_TEMPLATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    \"\"\"Standalone helper for an installed under-one skill bundle.\"\"\"

    from __future__ import annotations

    import json
    import re
    import subprocess
    import sys
    from pathlib import Path


    REQUIRED_META_FIELDS = [
        "id",
        "name",
        "version",
        "entry",
        "description",
        "triggers",
        "inputs",
        "outputs",
        "min_python",
    ]
    REQUIRED_SECTIONS = [
        "触发词",
        "功能概述",
        "工作流程",
        "输入输出",
        "API接口",
        "使用示例",
        "测试方法",
    ]


    def _root() -> Path:
        return Path(__file__).resolve().parent


    def _load_meta() -> dict:
        meta_path = _root() / "_skillhub_meta.json"
        if not meta_path.exists():
            return {}
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}


    def _audit() -> dict:
        root = _root()
        errors = []
        warnings = []
        files_checked = 0
        meta_version = None
        doc_version = None
        entry_rel = None

        skill_md = root / "SKILL.md"
        meta_json = root / "_skillhub_meta.json"
        scripts_dir = root / "scripts"

        if skill_md.exists():
            files_checked += 1
            text = skill_md.read_text(encoding="utf-8")
            for section in REQUIRED_SECTIONS:
                if f"## {section}" not in text:
                    warnings.append(f"SKILL.md missing recommended section: {section}")
            if "```mermaid" not in text:
                warnings.append("SKILL.md should include a mermaid architecture diagram")
            if "```" not in text:
                warnings.append("SKILL.md should include example code/input-output blocks")
            match = re.search(r'version:\\s*"?([0-9A-Za-z_.-]+)"?', text)
            if match:
                doc_version = match.group(1)
        else:
            errors.append("missing SKILL.md")

        meta = {}
        if meta_json.exists():
            files_checked += 1
            try:
                meta = json.loads(meta_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid _skillhub_meta.json: {exc}")
                meta = {}
            if isinstance(meta, dict):
                meta_version = str(meta.get("version")) if meta.get("version") is not None else None
                entry_rel = str(meta.get("entry") or "").strip() or None
                for field in REQUIRED_META_FIELDS:
                    if field not in meta:
                        errors.append(f"metadata missing required field: {field}")
                if meta.get("id") != root.name:
                    errors.append(f"metadata id mismatch: expected {root.name}, got {meta.get('id')}")
        else:
            errors.append("missing _skillhub_meta.json")

        if scripts_dir.exists():
            for script in scripts_dir.rglob("*.py"):
                if "legacy" in script.parts:
                    continue
                files_checked += 1
                try:
                    compile(script.read_text(encoding="utf-8"), str(script), "exec")
                except SyntaxError as exc:
                    errors.append(f"syntax error in {script.name}: {exc}")
        else:
            errors.append("missing scripts directory")

        if entry_rel:
            entry_path = root / entry_rel
            files_checked += 1
            if not entry_path.exists():
                errors.append(f"entry script missing: {entry_rel}")
            else:
                entry_text = entry_path.read_text(encoding="utf-8")
                if "record_metrics" not in entry_text and "record_metric_manual" not in entry_text:
                    warnings.append("entry script does not appear to record runtime metrics")

        return {
            "skill": root.name,
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "files_checked": files_checked,
            "meta_version": meta_version,
            "doc_version": doc_version,
        }


    def _print_report(payload) -> int:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload.get("ok", payload.get("passed", False)) else 1


    def validate() -> int:
        return _print_report(_audit())


    def self_test() -> int:
        test_script = _root() / "tests" / "self_test.py"
        if test_script.exists():
            result = subprocess.run([sys.executable, str(test_script)], cwd=str(_root()))
            return result.returncode
        return validate()


    def info() -> int:
        meta = _load_meta()
        if meta:
            return _print_report(meta)
        return _print_report({"ok": False, "error": "missing _skillhub_meta.json"})


    def main() -> int:
        command = sys.argv[1] if len(sys.argv) > 1 else "validate"
        if command == "validate":
            return validate()
        if command in {"self-test", "test"}:
            return self_test()
        if command == "info":
            return info()
        print("usage: skillctl.py [validate|self-test|info]", file=sys.stderr)
        return 2


    if __name__ == "__main__":
        raise SystemExit(main())
    """
)


SELF_TEST_TEMPLATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    \"\"\"Generic standalone self-test for an installed under-one skill.\"\"\"

    from __future__ import annotations

    import json
    import re
    from pathlib import Path


    ROOT = Path(__file__).resolve().parent.parent


    def main() -> int:
        errors = []
        warnings = []
        skill_md = ROOT / "SKILL.md"
        meta_json = ROOT / "_skillhub_meta.json"
        scripts_dir = ROOT / "scripts"

        assert skill_md.exists(), "missing SKILL.md"
        assert meta_json.exists(), "missing _skillhub_meta.json"
        meta = json.loads(meta_json.read_text(encoding="utf-8"))
        assert isinstance(meta, dict), "metadata must be an object"
        assert meta.get("id") == ROOT.name, f"id mismatch: {meta.get('id')} != {ROOT.name}"
        text = skill_md.read_text(encoding="utf-8")
        for section in ["触发词", "功能概述", "工作流程", "输入输出", "API接口", "使用示例", "测试方法"]:
            if f"## {section}" not in text:
                warnings.append(section)
        if "```mermaid" not in text:
            warnings.append("mermaid")
        for script in ROOT.rglob("*.py"):
            if "legacy" in script.parts:
                continue
            try:
                compile(script.read_text(encoding="utf-8"), str(script), "exec")
            except SyntaxError as exc:
                raise AssertionError(f"syntax error: {script}: {exc}") from exc
        if not scripts_dir.exists():
            errors.append("missing scripts")
        assert not errors, errors
        print("self-test passed")
        return 0


    if __name__ == "__main__":
        raise SystemExit(main())
    """
)


DELEGATED_SELF_TEST_TEMPLATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    \"\"\"Behavioral standalone self-test for an installed under-one skill.\"\"\"

    from __future__ import annotations

    import importlib.util
    import json
    import sys
    from pathlib import Path


    ROOT = Path(__file__).resolve().parent.parent
    ENTRY = {entry_path!r}
    SMOKE_PATH = {smoke_path!r}


    def _load_meta() -> dict:
        return json.loads((ROOT / "_skillhub_meta.json").read_text(encoding="utf-8"))


    def _load_module(script: Path, module_name: str):
        sys.path.insert(0, str(ROOT.parent))
        sys.path.insert(0, str(ROOT))
        spec = importlib.util.spec_from_file_location(module_name, script)
        assert spec is not None and spec.loader is not None, f"cannot load {{script}}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


    def _load_entry():
        script = ROOT / ENTRY
        assert script.exists(), f"missing entry script: {{ENTRY}}"
        module_name = f"standalone_selftest_{{ROOT.name}}_{{script.stem}}".replace("-", "_")
        return _load_module(script, module_name)


    def _load_smoke():
        script = ROOT / SMOKE_PATH
        assert script.exists(), f"missing standalone smoke script: {{SMOKE_PATH}}"
        module_name = f"standalone_smoke_{{ROOT.name}}_{{script.stem}}".replace("-", "_")
        return _load_module(script, module_name)


    def _validate_structure() -> None:
        assert (ROOT / "SKILL.md").exists(), "missing SKILL.md"
        assert (ROOT / "_skillhub_meta.json").exists(), "missing _skillhub_meta.json"
        assert (ROOT / ENTRY).exists(), f"missing entry script: {{ENTRY}}"
        assert (ROOT / SMOKE_PATH).exists(), f"missing standalone smoke script: {{SMOKE_PATH}}"


    def main() -> int:
        _validate_structure()
        meta = _load_meta()
        assert meta.get("id") == ROOT.name, f"id mismatch: {{meta.get('id')}} != {{ROOT.name}}"
        smoke = _load_smoke()
        runner = getattr(smoke, "run_smoke", None)
        assert callable(runner), "standalone smoke script must define run_smoke(root, load_entry, load_meta)"
        summary = runner(ROOT, _load_entry, _load_meta)
        print(f"self-test passed: {{summary}}")
        return 0


    if __name__ == "__main__":
        raise SystemExit(main())
    """
)


@dataclass
class ParsedSkillBundle:
    name: str
    version: str
    built_at: str
    files: Dict[str, str]


def iter_skill_files(skill_dir: Path):
    """Return bundleable files for a source skill directory."""
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in f.relative_to(skill_dir).parts):
            continue
        if any(f.name.endswith(suf) for suf in EXCLUDE_SUFFIXES):
            continue
        yield f.relative_to(skill_dir).as_posix(), f
    for relpath, helper in _iter_shared_helper_files(skill_dir):
        yield relpath, helper


def _detect_shared_helpers(skill_dir: Path) -> list[str]:
    required = set()
    patterns = {
        module: re.compile(rf"(^|\n)\s*(from|import)\s+{re.escape(module)}\b", flags=re.MULTILINE)
        for module in SHARED_HELPER_MODULES
    }
    for script in skill_dir.rglob("*.py"):
        if not script.is_file():
            continue
        text = script.read_text(encoding="utf-8")
        for module, pattern in patterns.items():
            if pattern.search(text):
                required.add(module)
    return [SHARED_HELPER_MODULES[module] for module in sorted(required)]


def _iter_shared_helper_files(skill_dir: Path):
    skills_root = skill_dir.parent
    for helper_name in _detect_shared_helpers(skill_dir):
        helper_path = skills_root / helper_name
        if not helper_path.exists():
            raise FileNotFoundError(f"missing shared helper for bundle: {helper_path}")
        yield f"{SHARED_PREFIX}{helper_name}", helper_path


def _build_self_test_text(parsed: ParsedSkillBundle) -> str:
    meta_text = parsed.files.get("_skillhub_meta.json")
    if not meta_text:
        return SELF_TEST_TEMPLATE
    try:
        meta = json.loads(meta_text)
    except json.JSONDecodeError:
        return SELF_TEST_TEMPLATE
    if not isinstance(meta, dict):
        return SELF_TEST_TEMPLATE
    entry_path = str(meta.get("entry") or "").strip()
    if not entry_path:
        return SELF_TEST_TEMPLATE
    standalone = meta.get("standalone_validation")
    if isinstance(standalone, dict):
        smoke_kind = str(standalone.get("kind") or "").strip()
        smoke_path = str(standalone.get("path") or "").strip()
        if smoke_kind == "python-script" and smoke_path:
            smoke_rel = Path(smoke_path).as_posix()
            if smoke_rel not in parsed.files:
                raise FileNotFoundError(f"standalone smoke script missing from bundle: {smoke_rel}")
            return DELEGATED_SELF_TEST_TEMPLATE.format(entry_path=entry_path, smoke_path=smoke_rel)
    return SELF_TEST_TEMPLATE


def build_bundle_text(skill_dir: Path, bundle_version: str = "v10.0.0") -> str:
    """Build a .skill bundle string from a source skill directory."""
    skill_dir = Path(skill_dir)
    files = list(iter_skill_files(skill_dir))
    if not files:
        raise RuntimeError(f"{skill_dir.name} 没有可打包的文件")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        BUNDLE_HEADER,
        f"name: {skill_dir.name}",
        f"version: {bundle_version}",
        f"built_at: {now}",
        f"files: {len(files)}",
        "=" * len(BUNDLE_HEADER),
        "",
    ]
    for rel, path in files:
        lines.append("")
        lines.append(f"{FILE_PREFIX}{rel}{FILE_SUFFIX}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            lines.append("<binary file skipped>")
            continue
        lines.append(content.rstrip("\n"))
    lines.append("")
    lines.append(BUNDLE_FOOTER)
    return "\n".join(lines) + "\n"


def _validate_relpath(relpath: str) -> Path:
    path = Path(relpath)
    if path.is_absolute():
        raise ValueError(f"bundle file path must be relative: {relpath}")
    if ".." in path.parts:
        raise ValueError(f"bundle file path must not traverse parents: {relpath}")
    return path


def parse_bundle_text(text: str) -> ParsedSkillBundle:
    lines = text.splitlines()
    if not lines or lines[0].strip() != BUNDLE_HEADER:
        raise ValueError("invalid skill bundle header")

    meta: Dict[str, str] = {}
    idx = 1
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if not line:
            continue
        if line.startswith("===="):
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()

    name = meta.get("name")
    version = meta.get("version", "")
    built_at = meta.get("built_at", "")
    if not name:
        raise ValueError("bundle metadata missing name")

    files: Dict[str, str] = {}
    current_path: str | None = None
    current_lines = []

    while idx < len(lines):
        line = lines[idx]
        idx += 1
        if line == BUNDLE_FOOTER:
            if current_path is not None:
                files[current_path] = "\n".join(current_lines).rstrip("\n") + "\n"
            current_path = None
            break
        if line.startswith(FILE_PREFIX) and line.endswith(FILE_SUFFIX):
            if current_path is not None:
                files[current_path] = "\n".join(current_lines).rstrip("\n") + "\n"
            current_path = line[len(FILE_PREFIX) : -len(FILE_SUFFIX)]
            _validate_relpath(current_path)
            current_lines = []
            continue
        if current_path is not None:
            current_lines.append(line)

    if not files:
        raise ValueError("bundle contains no files")

    return ParsedSkillBundle(name=name, version=version, built_at=built_at, files=files)


def install_bundle(bundle_path: Path, target_root: Path, force: bool = False) -> Dict[str, object]:
    parsed = parse_bundle_text(bundle_path.read_text(encoding="utf-8"))
    target_root.mkdir(parents=True, exist_ok=True)
    skill_dir = target_root / parsed.name

    if skill_dir.exists():
        if not force:
            raise FileExistsError(f"skill already exists: {skill_dir}")
        shutil.rmtree(skill_dir)

    written_files = []
    shared_files = []
    for relpath, content in parsed.files.items():
        rel = _validate_relpath(relpath)
        if relpath.startswith(SHARED_PREFIX):
            output_path = target_root / Path(relpath[len(SHARED_PREFIX) :])
            shared_files.append(str(output_path))
        else:
            output_path = skill_dir / rel
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        written_files.append(str(output_path))

    ctl_path = skill_dir / "skillctl.py"
    ctl_path.write_text(SKILLCTL_TEMPLATE, encoding="utf-8")
    ctl_path.chmod(0o755)
    written_files.append(str(ctl_path))

    tests_dir = skill_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    self_test_path = tests_dir / "self_test.py"
    self_test_path.write_text(_build_self_test_text(parsed), encoding="utf-8")
    self_test_path.chmod(0o755)
    written_files.append(str(self_test_path))

    manifest_path = skill_dir / "install-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "name": parsed.name,
                "version": parsed.version,
                "built_at": parsed.built_at,
                "source_bundle": str(bundle_path),
                "file_count": len(parsed.files),
                "shared_files": shared_files,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    written_files.append(str(manifest_path))

    return {
        "name": parsed.name,
        "version": parsed.version,
        "built_at": parsed.built_at,
        "target_dir": str(skill_dir),
        "file_count": len(written_files),
        "files": written_files,
    }


def verify_installed_skill(skill_dir: Path) -> Dict[str, object]:
    """Run validate and self-test for an installed standalone skill directory."""
    skill_dir = Path(skill_dir).resolve()
    skillctl = skill_dir / "skillctl.py"
    if not skillctl.exists():
        return {
            "passed": False,
            "skill": skill_dir.name,
            "error": f"missing skillctl.py: {skillctl}",
            "validate": {"returncode": 1, "stdout": "", "stderr": f"missing skillctl.py: {skillctl}"},
            "self_test": {"returncode": 1, "stdout": "", "stderr": f"missing skillctl.py: {skillctl}"},
        }

    validate = subprocess.run(
        [sys.executable, str(skillctl), "validate"],
        cwd=str(skill_dir),
        capture_output=True,
        text=True,
    )
    self_test = subprocess.run(
        [sys.executable, str(skillctl), "self-test"],
        cwd=str(skill_dir),
        capture_output=True,
        text=True,
    )
    return {
        "passed": validate.returncode == 0 and self_test.returncode == 0,
        "skill": skill_dir.name,
        "validate": {
            "returncode": validate.returncode,
            "stdout": validate.stdout.strip(),
            "stderr": validate.stderr.strip(),
        },
        "self_test": {
            "returncode": self_test.returncode,
            "stdout": self_test.stdout.strip(),
            "stderr": self_test.stderr.strip(),
        },
    }


def verify_bundle_roundtrip(skill_dir: Path, bundle_version: str = "v10.0.0") -> Dict[str, object]:
    """Build a source skill into a bundle, install it into a temp dir, then validate/self-test it."""
    skill_dir = Path(skill_dir).resolve()
    with tempfile.TemporaryDirectory(prefix=f"{skill_dir.name}-bundle-") as tmp:
        tmp_root = Path(tmp)
        bundle_path = tmp_root / f"{skill_dir.name}.skill"
        install_root = tmp_root / "installed"
        bundle_path.write_text(build_bundle_text(skill_dir, bundle_version=bundle_version), encoding="utf-8")
        install_result = install_bundle(bundle_path, install_root, force=True)
        installed_skill_dir = Path(str(install_result["target_dir"]))
        installed_check = verify_installed_skill(installed_skill_dir)
        return {
            "passed": installed_check["passed"],
            "skill": skill_dir.name,
            "bundle_path": str(bundle_path),
            "installed_dir": str(installed_skill_dir),
            "installed_file_count": install_result["file_count"],
            "validate": installed_check["validate"],
            "self_test": installed_check["self_test"],
        }
