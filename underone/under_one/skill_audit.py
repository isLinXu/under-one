"""Skill governance audit helpers.

Validate the packaged skill layout, metadata consistency, and a few
lightweight operational conventions so the skill ecosystem can be checked
before release or extension.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


REQUIRED_META_FIELDS = {
    "id": str,
    "name": str,
    "version": str,
    "entry": str,
    "description": str,
    "triggers": list,
    "inputs": list,
    "outputs": list,
    "min_python": str,
}

REQUIRED_SKILL_SECTIONS = [
    "触发词",
    "功能概述",
    "工作流程",
    "输入输出",
    "API接口",
    "使用示例",
    "测试方法",
]

REQUIRED_ALIGNMENT_FIELDS = [
    "core",
    "agent_meaning",
    "cost",
    "boundary",
]

BOOTSTRAP_PROFILE_FIELDS = [
    "avg_quality",
    "avg_completeness",
    "avg_consistency",
    "avg_human",
    "success_rate",
    "avg_duration",
    "recommended_min_records",
]

CONTROL_PLANE_FIELDS = [
    "role",
    "scope",
    "reads",
    "writes",
    "handoff_targets",
    "mutation_gate",
    "will_not",
    "summary",
]

ENGINE_OPT_IN_FIELDS = [
    "env",
    "flag",
    "redirect_entry",
]

CONTROL_PLANE_SKILLS = {
    "qiti-yuanliu",
    "bagua-zhen",
    "xiushen-lu",
}


@dataclass
class SkillAuditResult:
    skill: str
    ok: bool
    errors: List[str]
    warnings: List[str]
    files_checked: int
    meta_version: Optional[str] = None
    doc_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def find_skills_root(start: Optional[Path] = None) -> Path:
    """Locate the `underone/skills` directory."""
    base = (start or Path(__file__).resolve()).resolve()
    candidates = [
        base.parent.parent / "skills",
        Path.cwd() / "underone" / "skills",
        Path.cwd() / "skills",
        Path.home() / ".under-one" / "skills",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    raise RuntimeError("找不到 underone/skills 目录")


def iter_skill_dirs(skills_root: Path) -> List[Path]:
    """Return actual skill directories only."""
    dirs: List[Path] = []
    for path in sorted(skills_root.iterdir()):
        if not path.is_dir():
            continue
        if (path / "SKILL.md").exists() or (path / "_skillhub_meta.json").exists():
            dirs.append(path)
    return dirs


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("metadata must be a JSON object")
    return data


def _extract_frontmatter_text(markdown: str) -> Optional[str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError:
        return None
    return "\n".join(lines[1:end_idx])


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in inner.split(",")]
    return value


def _parse_frontmatter(markdown_path: Path) -> Dict[str, Any]:
    text = markdown_path.read_text(encoding="utf-8")
    frontmatter = _extract_frontmatter_text(text)
    if not frontmatter:
        return {}

    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(frontmatter) or {}
        return parsed if isinstance(parsed, dict) else {}
    except ImportError:
        pass

    # Minimal parser for this repo's SKILL.md frontmatter shape.
    root: Dict[str, Any] = {}
    current_section: Optional[str] = None
    for raw_line in frontmatter.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0 and line.endswith(":"):
            current_section = line[:-1].strip()
            root[current_section] = {}
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        parsed = _parse_scalar(value)
        if indent > 0 and current_section:
            section = root.setdefault(current_section, {})
            if isinstance(section, dict):
                section[key.strip()] = parsed
        else:
            root[key.strip()] = parsed
    return root


def _extract_h2_sections(markdown_text: str) -> List[str]:
    sections: List[str] = []
    for line in markdown_text.splitlines():
        if line.startswith("## "):
            sections.append(line[3:].strip())
    return sections


def _extract_section(markdown_text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\s*$"
    lines = markdown_text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if re.match(pattern, line):
            start = idx + 1
            break
    if start is None:
        return ""
    collected: List[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def _normalize_doc_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _check_doc_io_consistency(markdown_text: str, meta: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    io_section = _extract_section(markdown_text, "输入输出")
    if not io_section:
        return warnings

    normalized = _normalize_doc_text(io_section)
    for declared_input in meta.get("inputs", []):
        token = _normalize_doc_text(str(declared_input))
        if token and token not in normalized:
            warnings.append(f"SKILL.md 输入输出章节未提及 metadata input: {declared_input}")
    for declared_output in meta.get("outputs", []):
        token = _normalize_doc_text(str(declared_output))
        if token and token not in normalized:
            warnings.append(f"SKILL.md 输入输出章节未提及 metadata output: {declared_output}")
    return warnings


def write_audit_report(report: Dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def _check_required_meta(meta: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field, expected_type in REQUIRED_META_FIELDS.items():
        if field not in meta:
            errors.append(f"metadata missing required field: {field}")
            continue
        if not isinstance(meta[field], expected_type):
            errors.append(
                f"metadata field {field} type mismatch: expected {expected_type.__name__}"
            )
    return errors


def _validate_python_version(value: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+", value))


def _validate_bootstrap_profile(profile: Any) -> List[str]:
    if profile is None:
        return []
    if not isinstance(profile, dict):
        return ["metadata bootstrap_profile must be an object"]

    warnings: List[str] = []
    missing = [field for field in BOOTSTRAP_PROFILE_FIELDS if field not in profile]
    if missing:
        warnings.append("metadata bootstrap_profile missing fields: " + ", ".join(missing))

    for field, value in profile.items():
        if field not in BOOTSTRAP_PROFILE_FIELDS and field != "degradation_window":
            warnings.append(f"metadata bootstrap_profile has unknown field: {field}")
            continue
        if not isinstance(value, (int, float)):
            warnings.append(f"metadata bootstrap_profile field {field} must be numeric")
    return warnings


def _validate_control_plane_contract(skill_name: str, contract: Any) -> List[str]:
    if contract is None:
        return ["metadata missing control_plane_contract"] if skill_name in CONTROL_PLANE_SKILLS else []
    if not isinstance(contract, dict):
        return ["metadata control_plane_contract must be an object"]

    warnings: List[str] = []
    missing = [field for field in CONTROL_PLANE_FIELDS if field not in contract]
    if missing:
        warnings.append("metadata control_plane_contract missing fields: " + ", ".join(missing))
    for field in ("reads", "writes", "handoff_targets", "will_not"):
        value = contract.get(field)
        if value is not None and not isinstance(value, list):
            warnings.append(f"metadata control_plane_contract field {field} must be a list")
    for field in ("role", "scope", "mutation_gate", "summary"):
        value = contract.get(field)
        if value is not None and not isinstance(value, str):
            warnings.append(f"metadata control_plane_contract field {field} must be a string")
    return warnings


def _validate_engine_manifest(skill_name: str, manifest: Any) -> List[str]:
    if skill_name != "xiushen-lu":
        return []
    if manifest is None:
        return ["metadata missing engine_manifest"]
    if not isinstance(manifest, dict):
        return ["metadata engine_manifest must be an object"]
    warnings: List[str] = []
    if not isinstance(manifest.get("active_entry"), str):
        warnings.append("metadata engine_manifest.active_entry must be a string")
    for field in ("auxiliary_tools", "compatibility_shims", "deprecated_experiments"):
        value = manifest.get(field)
        if not isinstance(value, list):
            warnings.append(f"metadata engine_manifest field {field} must be a list")
    experimental_opt_in = manifest.get("experimental_opt_in")
    if experimental_opt_in is not None and not isinstance(experimental_opt_in, dict):
        warnings.append("metadata engine_manifest.experimental_opt_in must be an object")
    elif isinstance(experimental_opt_in, dict):
        missing = [field for field in ENGINE_OPT_IN_FIELDS if not isinstance(experimental_opt_in.get(field), str)]
        if missing:
            warnings.append(
                "metadata engine_manifest.experimental_opt_in missing or invalid fields: "
                + ", ".join(missing)
            )
    return warnings


def _validate_xiushen_engine_files(skill_dir: Path, manifest: Any) -> List[str]:
    if skill_dir.name != "xiushen-lu" or not isinstance(manifest, dict):
        return []

    warnings: List[str] = []
    active_entry = manifest.get("active_entry")
    if isinstance(active_entry, str):
        active_path = skill_dir / active_entry
        if not active_path.exists():
            warnings.append(f"engine manifest active_entry missing file: {active_entry}")

    experimental_opt_in = manifest.get("experimental_opt_in") or {}
    opt_in_tokens = []
    if isinstance(experimental_opt_in, dict):
        for field in ("env", "flag"):
            value = experimental_opt_in.get(field)
            if isinstance(value, str) and value:
                opt_in_tokens.append(value)

    for rel_path in manifest.get("deprecated_experiments", []):
        if not isinstance(rel_path, str):
            warnings.append("engine manifest deprecated_experiments must contain string paths")
            continue
        target = skill_dir / rel_path
        if not target.exists():
            warnings.append(f"engine manifest deprecated experiment missing file: {rel_path}")
            continue
        text = target.read_text(encoding="utf-8")
        if 'ENGINE_STATUS = "deprecated-experiment"' not in text:
            warnings.append(f"deprecated experiment missing ENGINE_STATUS marker: {rel_path}")
        if 'REPLACED_BY = "core_engine.py"' not in text:
            warnings.append(f"deprecated experiment missing REPLACED_BY marker: {rel_path}")
        if opt_in_tokens and not any(token in text for token in opt_in_tokens):
            warnings.append(f"deprecated experiment missing opt-in guard marker: {rel_path}")
    return warnings


def audit_skill_dir(skill_dir: Path) -> SkillAuditResult:
    """Audit a single skill directory."""
    errors: List[str] = []
    warnings: List[str] = []
    files_checked = 0
    meta_version = None
    doc_version = None

    skill_md = skill_dir / "SKILL.md"
    meta_json = skill_dir / "_skillhub_meta.json"
    scripts_dir = skill_dir / "scripts"

    for path in (skill_md, meta_json, scripts_dir):
        files_checked += 1
        if not path.exists():
            errors.append(f"missing required path: {path.name}")

    meta: Dict[str, Any] = {}
    if meta_json.exists():
        try:
            meta = _load_json(meta_json)
            meta_version = str(meta.get("version")) if meta.get("version") is not None else None
            errors.extend(_check_required_meta(meta))
            if meta.get("id") and meta["id"] != skill_dir.name:
                errors.append(f"metadata id mismatch: expected {skill_dir.name}, got {meta['id']}")
            if meta.get("min_python") and not _validate_python_version(str(meta["min_python"])):
                errors.append("metadata min_python must look like '3.8'")
            for field in ("triggers", "inputs", "outputs"):
                if isinstance(meta.get(field), list) and not meta[field]:
                    warnings.append(f"metadata field {field} should not be empty")
            alignment = meta.get("alignment")
            if not isinstance(alignment, dict):
                warnings.append("metadata missing alignment profile")
            else:
                missing_alignment_fields = [field for field in REQUIRED_ALIGNMENT_FIELDS if not alignment.get(field)]
                if missing_alignment_fields:
                    warnings.append(
                        "metadata alignment missing fields: " + ", ".join(missing_alignment_fields)
                    )
            warnings.extend(_validate_bootstrap_profile(meta.get("bootstrap_profile")))
            warnings.extend(_validate_control_plane_contract(skill_dir.name, meta.get("control_plane_contract")))
            warnings.extend(_validate_engine_manifest(skill_dir.name, meta.get("engine_manifest")))
            warnings.extend(_validate_xiushen_engine_files(skill_dir, meta.get("engine_manifest")))
        except Exception as exc:
            errors.append(f"invalid _skillhub_meta.json: {exc}")

    frontmatter = {}
    if skill_md.exists():
        files_checked += 1
        markdown_text = skill_md.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(skill_md)
        if not frontmatter:
            warnings.append("SKILL.md has no parseable frontmatter")
        metadata = frontmatter.get("metadata", frontmatter)
        if isinstance(metadata, dict):
            if metadata.get("name"):
                doc_name = str(metadata["name"])
                if meta.get("id") and doc_name != meta["id"]:
                    warnings.append(f"SKILL.md metadata.name differs from metadata id: {doc_name}")
            if metadata.get("version") is not None:
                doc_version = str(metadata["version"])
        else:
            warnings.append("SKILL.md frontmatter metadata section is not an object")

        sections = _extract_h2_sections(markdown_text)
        missing_sections = [section for section in REQUIRED_SKILL_SECTIONS if section not in sections]
        if missing_sections:
            warnings.append(f"SKILL.md missing recommended sections: {', '.join(missing_sections)}")
        if "```mermaid" not in markdown_text:
            warnings.append("SKILL.md should include a mermaid architecture diagram")
        if markdown_text.count("```") < 4:
            warnings.append("SKILL.md should include example code/input-output blocks")
        warnings.extend(_check_doc_io_consistency(markdown_text, meta))

    if meta and meta.get("entry"):
        entry_path = skill_dir / str(meta["entry"])
        files_checked += 1
        if not entry_path.exists():
            errors.append(f"entry script missing: {meta['entry']}")
        else:
            entry_text = entry_path.read_text(encoding="utf-8")
            if "record_metrics" not in entry_text and "record_metric_manual" not in entry_text:
                warnings.append("entry script does not appear to record runtime metrics")

    if doc_version and meta_version and doc_version != meta_version:
        warnings.append(
            f"version drift between SKILL.md ({doc_version}) and _skillhub_meta.json ({meta_version})"
        )

    return SkillAuditResult(
        skill=skill_dir.name,
        ok=not errors,
        errors=errors,
        warnings=warnings,
        files_checked=files_checked,
        meta_version=meta_version,
        doc_version=doc_version,
    )


def audit_skills_root(skills_root: Path) -> Dict[str, Any]:
    """Audit all skill directories under a root."""
    results = [audit_skill_dir(skill_dir) for skill_dir in iter_skill_dirs(skills_root)]
    ok_count = sum(1 for result in results if result.ok)
    warning_count = sum(len(result.warnings) for result in results)
    error_count = sum(len(result.errors) for result in results)
    return {
        "ok": error_count == 0,
        "skills_root": str(skills_root),
        "skill_count": len(results),
        "ok_count": ok_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "results": [result.to_dict() for result in results],
    }
