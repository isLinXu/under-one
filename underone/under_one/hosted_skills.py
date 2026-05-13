"""Host runtime adapters for installing under-one skills into multiple products."""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .skill_bundle import build_bundle_text, install_bundle, resolve_bundle_version, verify_installed_skill
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


@dataclass(frozen=True)
class HostProfile:
    name: str
    label: str
    layout: str
    default_root_factory: Optional[Callable[[], Path]]
    uses_agents_yaml: bool = False


def _home_root(*parts: str) -> Path:
    return Path.home().joinpath(*parts).expanduser()


HOST_PROFILES: Dict[str, HostProfile] = {
    "codex": HostProfile("codex", "Codex", "frontmatter", lambda: _home_root(".codex", "skills"), True),
    "workbuddy": HostProfile("workbuddy", "WorkBuddy", "frontmatter", lambda: _home_root(".workbuddy", "skills")),
    "qclaw": HostProfile("qclaw", "QClaw", "passthrough", lambda: _home_root(".qclaw", "skills")),
    "custom": HostProfile("custom", "Custom", "passthrough", None),
    "native": HostProfile("native", "Native", "passthrough", None),
}

HOST_ALIASES = {
    "openclaw": "qclaw",
    "claw": "qclaw",
    "work-buddy": "workbuddy",
    "wb": "workbuddy",
    "third-party": "custom",
    "thirdparty": "custom",
    "source": "native",
}


def available_hosts() -> List[str]:
    return [name for name in HOST_PROFILES if name != "native"]


def accepted_host_names() -> List[str]:
    names = available_hosts()
    for alias, target in HOST_ALIASES.items():
        if target in names and alias not in names:
            names.append(alias)
    return names


def host_aliases_for(host: str) -> List[str]:
    canonical = resolve_host_name(host)
    return [alias for alias, target in HOST_ALIASES.items() if target == canonical]


def resolve_host_name(host: str) -> str:
    key = host.strip().lower()
    key = HOST_ALIASES.get(key, key)
    if key not in HOST_PROFILES:
        raise ValueError(f"unknown host runtime: {host}")
    return key


def get_host_profile(host: str) -> HostProfile:
    return HOST_PROFILES[resolve_host_name(host)]


def default_host_skills_root(host: str) -> Path:
    profile = get_host_profile(host)
    if profile.default_root_factory is None:
        raise ValueError(f"host runtime has no default root: {host}")
    return profile.default_root_factory()


def resolve_host_target_root(host: str, target_root: Path | str | None = None) -> Path:
    if target_root is not None:
        return Path(target_root).expanduser().resolve()
    profile = get_host_profile(host)
    if profile.default_root_factory is None:
        raise ValueError(f"host runtime '{profile.name}' requires --dest /path/to/skills")
    return profile.default_root_factory().expanduser().resolve()


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


def _build_description(meta: Dict[str, Any]) -> str:
    base = str(meta.get("description") or meta.get("name") or "").strip()
    triggers = [str(item).strip() for item in meta.get("triggers", []) if str(item).strip()]
    if not triggers:
        return base
    return f"{base} Use when the user asks for {'、'.join(triggers[:6])}."


def build_host_skill_markdown(skill_dir: Path, host: str) -> str:
    skill_dir = Path(skill_dir).resolve()
    profile = get_host_profile(host)
    source_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    if profile.layout == "passthrough":
        return source_text if source_text.endswith("\n") else source_text + "\n"

    meta = _load_skillhub_meta(skill_dir)
    body = _strip_frontmatter(source_text)
    frontmatter = [
        "---",
        f'name: {_yaml_scalar(meta.get("id") or skill_dir.name)}',
        f'description: {_yaml_scalar(_build_description(meta))}',
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
        f'  host: {_yaml_scalar(profile.name)}',
        "---",
        "",
    ]
    return "\n".join(frontmatter) + body.rstrip() + "\n"


def build_host_extra_files(skill_dir: Path, host: str) -> Dict[str, str]:
    profile = get_host_profile(host)
    if not profile.uses_agents_yaml:
        return {}
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
    return {"agents/openai.yaml": "\n".join(lines)}


def verify_host_skill_install(skill_dir: Path, host: str) -> Dict[str, Any]:
    skill_dir = Path(skill_dir).resolve()
    profile = get_host_profile(host)
    errors: List[str] = []
    warnings: List[str] = []
    files_checked = 0

    skill_md = skill_dir / "SKILL.md"
    meta_json = skill_dir / "_skillhub_meta.json"
    agents_yaml = skill_dir / "agents" / "openai.yaml"

    parsed_name = None
    parsed_description = None

    if not skill_md.exists():
        errors.append("missing SKILL.md")
    else:
        files_checked += 1
        text = skill_md.read_text(encoding="utf-8")
        if profile.layout == "frontmatter":
            frontmatter = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, flags=re.DOTALL)
            if frontmatter is None:
                errors.append("SKILL.md missing YAML frontmatter")
            else:
                block = frontmatter.group(1)
                name_match = re.search(r"(?m)^name:\s*(.+)$", block)
                desc_match = re.search(r"(?m)^description:\s*(.+)$", block)
                parsed_name = json.loads(name_match.group(1)) if name_match else None
                parsed_description = json.loads(desc_match.group(1)) if desc_match else None
                if not parsed_name:
                    errors.append("SKILL.md missing top-level name")
                elif parsed_name != skill_dir.name:
                    errors.append(f"name mismatch: expected {skill_dir.name}, got {parsed_name}")
                if not parsed_description:
                    errors.append("SKILL.md missing top-level description")
        elif "metadata:" not in text:
            warnings.append("native SKILL.md should keep source metadata block")

    meta_payload: Dict[str, Any] = {}
    if not meta_json.exists():
        errors.append("missing _skillhub_meta.json")
    else:
        files_checked += 1
        try:
            meta_payload = json.loads(meta_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid _skillhub_meta.json: {exc}")
        if profile.layout == "passthrough" and isinstance(meta_payload, dict):
            parsed_name = str(meta_payload.get("id") or skill_dir.name)
            parsed_description = str(meta_payload.get("description") or meta_payload.get("name") or "").strip() or None

    if profile.uses_agents_yaml:
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
    if parsed_description and triggers and profile.layout == "frontmatter":
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
        "host": profile.name,
        "skill": skill_dir.name,
        "files_checked": files_checked,
        "name": parsed_name,
        "description": parsed_description,
        "errors": errors,
        "warnings": warnings,
    }


def _augment_install_manifest(
    installed_dir: Path,
    *,
    host: str,
    source_skill_dir: Path,
    bundle_version: str,
    extra_files: Dict[str, str],
) -> None:
    manifest_path = installed_dir / "install-manifest.json"
    if not manifest_path.exists():
        return
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {}
    payload["host_runtime"] = {
        "host": host,
        "source_skill_dir": str(source_skill_dir),
        "bundle_version": bundle_version,
        "layout": get_host_profile(host).layout,
        "extra_files": sorted(extra_files.keys()),
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def install_host_skill(
    source_skill_dir: Path,
    host: str,
    target_root: Path | None = None,
    *,
    force: bool = False,
    bundle_version: str | None = None,
) -> Dict[str, Any]:
    source_skill_dir = Path(source_skill_dir).resolve()
    profile = get_host_profile(host)
    target_root = resolve_host_target_root(profile.name, target_root)
    resolved_bundle_version = resolve_bundle_version(source_skill_dir, bundle_version)

    with tempfile.TemporaryDirectory(prefix=f"{source_skill_dir.name}-{profile.name}-install-") as tmp:
        bundle_path = Path(tmp) / f"{source_skill_dir.name}.skill"
        bundle_path.write_text(
            build_bundle_text(source_skill_dir, bundle_version=resolved_bundle_version),
            encoding="utf-8",
        )
        install_result = install_bundle(bundle_path, target_root, force=force)

    installed_dir = Path(str(install_result["target_dir"])).resolve()
    installed_md = build_host_skill_markdown(source_skill_dir, profile.name)
    (installed_dir / "SKILL.md").write_text(installed_md, encoding="utf-8")

    extra_files = build_host_extra_files(source_skill_dir, profile.name)
    for relpath, content in extra_files.items():
        output_path = installed_dir / relpath
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    _augment_install_manifest(
        installed_dir,
        host=profile.name,
        source_skill_dir=source_skill_dir,
        bundle_version=resolved_bundle_version,
        extra_files=extra_files,
    )

    host_validation = verify_host_skill_install(installed_dir, profile.name)
    return {
        "skill": source_skill_dir.name,
        "host": profile.name,
        "installed_dir": str(installed_dir),
        "target_root": str(target_root),
        "bundle_version": resolved_bundle_version,
        "install_result": install_result,
        "installed_lifecycle": verify_installed_skill(installed_dir),
        "host_validation": host_validation,
    }


def install_and_validate_host_skill(
    source_skill_dir: Path,
    host: str,
    target_root: Path | None = None,
    *,
    force: bool = False,
    bundle_version: str | None = None,
    include_source_validation: bool = True,
) -> Dict[str, Any]:
    source_skill_dir = Path(source_skill_dir).resolve()
    install_report = install_host_skill(
        source_skill_dir,
        host,
        target_root=target_root,
        force=force,
        bundle_version=bundle_version,
    )
    source_validation = None
    if include_source_validation:
        source_validation = validate_skill(source_skill_dir.name, source_skill_dir)
    overall_passed = (
        install_report["installed_lifecycle"]["passed"]
        and install_report["host_validation"]["passed"]
        and (source_validation is None or source_validation["validation_passed"])
    )
    return {
        "skill": source_skill_dir.name,
        "host": get_host_profile(host).name,
        "installed_dir": install_report["installed_dir"],
        "overall_passed": overall_passed,
        "install": install_report,
        "source_validation": source_validation,
    }


def iter_source_skill_dirs(skills_root: Path, skill_names: Iterable[str] | None = None) -> Iterable[Path]:
    selected = list(skill_names or DEFAULT_SKILLS)
    for name in selected:
        yield (Path(skills_root) / name).resolve()


def build_codex_skill_markdown(skill_dir: Path) -> str:
    return build_host_skill_markdown(skill_dir, "codex")


def build_openai_yaml(skill_dir: Path) -> str:
    extra = build_host_extra_files(skill_dir, "codex")
    return extra["agents/openai.yaml"]


def verify_codex_skill_install(skill_dir: Path) -> Dict[str, Any]:
    return verify_host_skill_install(skill_dir, "codex")


def default_codex_skills_root() -> Path:
    return default_host_skills_root("codex")


def install_codex_skill(
    source_skill_dir: Path,
    target_root: Path | None = None,
    *,
    force: bool = False,
    bundle_version: str | None = None,
) -> Dict[str, Any]:
    report = install_host_skill(
        source_skill_dir,
        "codex",
        target_root=target_root,
        force=force,
        bundle_version=bundle_version,
    )
    report["codex_validation"] = report.pop("host_validation")
    return report


def install_and_validate_codex_skill(
    source_skill_dir: Path,
    target_root: Path | None = None,
    *,
    force: bool = False,
    bundle_version: str | None = None,
    include_source_validation: bool = True,
) -> Dict[str, Any]:
    report = install_and_validate_host_skill(
        source_skill_dir,
        "codex",
        target_root=target_root,
        force=force,
        bundle_version=bundle_version,
        include_source_validation=include_source_validation,
    )
    report["install"]["codex_validation"] = report["install"].pop("host_validation")
    return report
