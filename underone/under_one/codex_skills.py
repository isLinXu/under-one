"""Codex-compatible installation helpers for under-one skills."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .skill_bundle import build_bundle_text, install_bundle, verify_installed_skill
from .skill_lifecycle import validate_skill


DEFAULT_SKILLS: List[str] = [
    "bagua-zhen",
    "dalu-dongguan",
    "fenghou-qimen",
    "juling-qianjiang",
    "liuku-xianzei",
    "qiti-yuanliu",
    "shenji-bailian",
    "shuangquanshou",
    "tongtian-lu",
    "xiushen-lu",
]


def default_codex_skills_root() -> Path:
    codex_home = Path.home() / ".codex"
    return (Path(codex_home) / "skills").expanduser()


def _load_skillhub_meta(skill_dir: Path) -> Dict[str, Any]:
    meta_path = skill_dir / "_skillhub_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"missing _skillhub_meta.json: {meta_path}")
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid metadata payload: {meta_path}")
    return payload


def _strip_frontmatter(text: str) -> str:
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", text, flags=re.DOTALL)
    if match:
        return text[match.end() :].lstrip("\n")
    return text.lstrip("\n")


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def _build_codex_description(meta: Dict[str, Any]) -> str:
    base = str(meta.get("description") or meta.get("name") or "").strip()
    triggers = [str(item).strip() for item in meta.get("triggers", []) if str(item).strip()]
    if not triggers:
        return base
    return f"{base} Use when the user asks for {'、'.join(triggers[:6])}."


def build_codex_skill_markdown(skill_dir: Path) -> str:
    skill_dir = Path(skill_dir).resolve()
    meta = _load_skillhub_meta(skill_dir)
    source_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    body = _strip_frontmatter(source_text)

    frontmatter = [
        "---",
        f'name: {_yaml_scalar(meta.get("id") or skill_dir.name)}',
        f'description: {_yaml_scalar(_build_codex_description(meta))}',
        "metadata:",
        f'  display_name: {_yaml_scalar(meta.get("name") or skill_dir.name)}',
        f'  version: {_yaml_scalar(meta.get("version") or "")}',
        f'  author: {_yaml_scalar(meta.get("author") or "under-one")}',
        f'  entry: {_yaml_scalar(meta.get("entry") or "")}',
        f'  language: {_yaml_scalar(meta.get("language") or "python")}',
        f'  tags: {_yaml_scalar(meta.get("tags") or [])}',
        f'  triggers: {_yaml_scalar(meta.get("triggers") or [])}',
        f'  inputs: {_yaml_scalar(meta.get("inputs") or [])}',
        f'  outputs: {_yaml_scalar(meta.get("outputs") or [])}',
        f'  min_python: {_yaml_scalar(meta.get("min_python") or "")}',
        "---",
        "",
    ]
    return "\n".join(frontmatter) + body.rstrip() + "\n"


def build_openai_yaml(skill_dir: Path) -> str:
    skill_dir = Path(skill_dir).resolve()
    meta = _load_skillhub_meta(skill_dir)
    triggers = [str(item).strip() for item in meta.get("triggers", []) if str(item).strip()]
    primary_trigger = triggers[0] if triggers else str(meta.get("name") or skill_dir.name)
    lines = [
        "interface:",
        f'  display_name: {_yaml_scalar(meta.get("name") or skill_dir.name)}',
        f'  short_description: {_yaml_scalar(str(meta.get("description") or "").strip())}',
        f'  default_prompt: {_yaml_scalar(f"使用 ${skill_dir.name} 处理“{primary_trigger}”场景，并返回结构化结果。")}',
        "",
    ]
    return "\n".join(lines)


def _extract_frontmatter_block(text: str) -> str | None:
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, flags=re.DOTALL)
    if not match:
        return None
    return match.group(1)


def _extract_top_level_value(frontmatter: str, key: str) -> str | None:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*(.+)$")
    match = pattern.search(frontmatter)
    if not match:
        return None
    raw = match.group(1).strip()
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip('"')
    return raw.strip("'")


def verify_codex_skill_install(skill_dir: Path) -> Dict[str, Any]:
    skill_dir = Path(skill_dir).resolve()
    errors: List[str] = []
    warnings: List[str] = []
    files_checked = 0

    skill_md = skill_dir / "SKILL.md"
    agents_yaml = skill_dir / "agents" / "openai.yaml"
    meta_json = skill_dir / "_skillhub_meta.json"

    parsed_name = None
    parsed_description = None

    if not skill_md.exists():
        errors.append("missing SKILL.md")
    else:
        files_checked += 1
        text = skill_md.read_text(encoding="utf-8")
        frontmatter = _extract_frontmatter_block(text)
        if frontmatter is None:
            errors.append("SKILL.md missing YAML frontmatter")
        else:
            parsed_name = _extract_top_level_value(frontmatter, "name")
            parsed_description = _extract_top_level_value(frontmatter, "description")
            if not parsed_name:
                errors.append("SKILL.md missing top-level name")
            elif parsed_name != skill_dir.name:
                errors.append(f"name mismatch: expected {skill_dir.name}, got {parsed_name}")
            if not parsed_description:
                errors.append("SKILL.md missing top-level description")

    meta_payload: Dict[str, Any] = {}
    if not meta_json.exists():
        errors.append("missing _skillhub_meta.json")
    else:
        files_checked += 1
        try:
            meta_payload = json.loads(meta_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid _skillhub_meta.json: {exc}")

    if not agents_yaml.exists():
        errors.append("missing agents/openai.yaml")
    else:
        files_checked += 1
        yaml_text = agents_yaml.read_text(encoding="utf-8")
        for marker in ["display_name:", "short_description:", "default_prompt:"]:
            if marker not in yaml_text:
                errors.append(f"agents/openai.yaml missing {marker.rstrip(':')}")
        if "$" not in yaml_text:
            warnings.append("agents/openai.yaml default_prompt should reference the skill handle")

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        warnings.append("missing scripts directory")
    else:
        for script in scripts_dir.rglob("*.py"):
            files_checked += 1
            try:
                compile(script.read_text(encoding="utf-8"), str(script), "exec")
            except SyntaxError as exc:
                errors.append(f"syntax error in {script.name}: {exc}")

    triggers = [str(item).strip() for item in meta_payload.get("triggers", []) if str(item).strip()]
    if parsed_description and triggers:
        if not any(trigger in parsed_description for trigger in triggers[:3]):
            warnings.append("description does not include primary trigger keywords")

    alignment = meta_payload.get("alignment")
    if not isinstance(alignment, dict):
        warnings.append("source metadata missing alignment profile")
    else:
        for field in ("core", "agent_meaning", "cost", "boundary"):
            if not alignment.get(field):
                warnings.append(f"source metadata alignment missing field: {field}")

    return {
        "passed": len(errors) == 0,
        "skill": skill_dir.name,
        "files_checked": files_checked,
        "name": parsed_name,
        "description": parsed_description,
        "errors": errors,
        "warnings": warnings,
    }


def install_codex_skill(
    source_skill_dir: Path,
    target_root: Path | None = None,
    *,
    force: bool = False,
    bundle_version: str = "v10.0.0",
) -> Dict[str, Any]:
    source_skill_dir = Path(source_skill_dir).resolve()
    target_root = (target_root or default_codex_skills_root()).expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix=f"{source_skill_dir.name}-codex-install-") as tmp:
        bundle_path = Path(tmp) / f"{source_skill_dir.name}.skill"
        bundle_path.write_text(build_bundle_text(source_skill_dir, bundle_version=bundle_version), encoding="utf-8")
        install_result = install_bundle(bundle_path, target_root, force=force)

    installed_dir = Path(str(install_result["target_dir"])).resolve()
    (installed_dir / "SKILL.md").write_text(build_codex_skill_markdown(source_skill_dir), encoding="utf-8")
    agents_dir = installed_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "openai.yaml").write_text(build_openai_yaml(source_skill_dir), encoding="utf-8")

    return {
        "skill": source_skill_dir.name,
        "installed_dir": str(installed_dir),
        "target_root": str(target_root),
        "bundle_version": bundle_version,
        "install_result": install_result,
        "installed_lifecycle": verify_installed_skill(installed_dir),
        "codex_validation": verify_codex_skill_install(installed_dir),
    }


def install_and_validate_codex_skill(
    source_skill_dir: Path,
    target_root: Path | None = None,
    *,
    force: bool = False,
    bundle_version: str = "v10.0.0",
    include_source_validation: bool = True,
) -> Dict[str, Any]:
    source_skill_dir = Path(source_skill_dir).resolve()
    install_report = install_codex_skill(
        source_skill_dir,
        target_root=target_root,
        force=force,
        bundle_version=bundle_version,
    )
    source_validation = None
    if include_source_validation:
        source_validation = validate_skill(source_skill_dir.name, source_skill_dir)
    overall_passed = (
        install_report["installed_lifecycle"]["passed"]
        and install_report["codex_validation"]["passed"]
        and (source_validation is None or source_validation["validation_passed"])
    )
    return {
        "skill": source_skill_dir.name,
        "installed_dir": install_report["installed_dir"],
        "overall_passed": overall_passed,
        "install": install_report,
        "source_validation": source_validation,
    }


def iter_source_skill_dirs(skills_root: Path, skill_names: Iterable[str] | None = None) -> Iterable[Path]:
    selected = list(skill_names or DEFAULT_SKILLS)
    for name in selected:
        yield (Path(skills_root) / name).resolve()
