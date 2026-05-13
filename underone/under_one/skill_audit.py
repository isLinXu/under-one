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
