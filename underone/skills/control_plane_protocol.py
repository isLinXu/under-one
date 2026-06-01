#!/usr/bin/env python3
"""Shared control-plane protocol for observer / coordinator / evolver skills."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from _skill_config import get_skill_config
except ImportError:
    def get_skill_config(_skill_name: str, key: str = None, default=None):
        return default


CONTROL_PLANE_CONTRACTS: Dict[str, Dict[str, Any]] = {
    "qiti-yuanliu": {
        "role": "observer",
        "scope": "context-diagnosis",
        "reads": ["context", "runtime_data"],
        "writes": ["runtime_data", "health_report"],
        "handoff_targets": ["dalu-dongguan", "xiushen-lu"],
        "mutation_gate": "diagnose-and-handoff-only",
        "will_not": ["write_skills", "persist_thresholds", "override_ecosystem_policy"],
        "summary": "负责诊断、稳态契约与 handoff，不直接改写 skill 代码或全局阈值。",
    },
    "bagua-zhen": {
        "role": "coordinator",
        "scope": "ecosystem-readonly",
        "reads": ["runtime_data", "shared_relationships"],
        "writes": ["ecosystem_report", "dashboard_artifacts"],
        "handoff_targets": ["juling-qianjiang", "xiushen-lu"],
        "mutation_gate": "report-only",
        "will_not": ["write_skills", "persist_thresholds", "rewrite_goal_anchor"],
        "summary": "负责聚合、仲裁与监控，不直接修改单个 skill 的内部实现。",
    },
    "xiushen-lu": {
        "role": "evolver",
        "scope": "cross-skill-evolution",
        "reads": ["runtime_data", "skills", "shared_knowledge"],
        "writes": ["evolution_report", "adaptive_thresholds", "skills_when_apply"],
        "handoff_targets": [],
        "mutation_gate": "explicit-apply-only",
        "will_not": ["rewrite_live_context", "bypass_manual_gate", "mutate_without_backup"],
        "summary": "负责分析与提出跨 skill 演化建议，仅在显式 apply 模式下改写技能内容。",
    },
}

_SECTION_MAP = {
    "qiti-yuanliu": "qitiyuanliu",
    "bagua-zhen": "baguazhen",
    "xiushen-lu": "xiushenlu",
}

_CONFIG_KEYS = {
    "role": "control_plane_role",
    "scope": "control_plane_scope",
    "reads": "control_plane_reads",
    "writes": "control_plane_writes",
    "handoff_targets": "control_plane_handoff_targets",
    "mutation_gate": "control_plane_mutation_gate",
    "will_not": "control_plane_will_not",
    "summary": "control_plane_summary",
}


def _normalize_contract(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    normalized: Dict[str, Any] = {}
    for key in ("role", "scope", "mutation_gate", "summary"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            normalized[key] = value.strip()
    for key in ("reads", "writes", "handoff_targets", "will_not"):
        value = raw.get(key)
        if isinstance(value, list):
            normalized[key] = [str(item).strip() for item in value if str(item).strip()]
    return normalized or None


def _load_meta_contract(skill_name: str, skill_dir: Optional[Path | str] = None) -> Optional[Dict[str, Any]]:
    if skill_dir:
        candidate = Path(skill_dir).expanduser().resolve()
    else:
        candidate = Path(__file__).resolve().parent / skill_name
    meta_path = candidate / "_skillhub_meta.json"
    if not meta_path.exists():
        return None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return _normalize_contract(payload.get("control_plane_contract"))


def _load_config_contract(skill_name: str) -> Optional[Dict[str, Any]]:
    section = _SECTION_MAP.get(skill_name)
    if not section:
        return None
    cfg = get_skill_config(section, default={}) or {}
    if not isinstance(cfg, dict):
        return None
    contract: Dict[str, Any] = {}
    for field, config_key in _CONFIG_KEYS.items():
        value = cfg.get(config_key)
        if value is None:
            continue
        if field in {"reads", "writes", "handoff_targets", "will_not"}:
            if isinstance(value, list):
                contract[field] = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            contract[field] = value.strip()
    return contract or None


def get_control_plane_contract(skill_name: str, skill_dir: Optional[Path | str] = None) -> Dict[str, Any]:
    contract: Dict[str, Any] = deepcopy(CONTROL_PLANE_CONTRACTS.get(skill_name, {}))
    meta_contract = _load_meta_contract(skill_name, skill_dir=skill_dir)
    if meta_contract:
        contract.update(meta_contract)
    config_contract = _load_config_contract(skill_name)
    if config_contract:
        contract.update(config_contract)
    return contract


def build_control_plane_status(
    skill_name: str,
    *,
    phase: str,
    manual_gate_required: bool,
    skill_dir: Optional[Path | str] = None,
    writes_applied: bool = False,
    next_owner: Optional[str] = None,
    handoff_targets: Optional[List[str]] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    contract = get_control_plane_contract(skill_name, skill_dir=skill_dir)
    contract_handoffs = list(contract.get("handoff_targets", []))
    explicit_handoffs = [str(item).strip() for item in (handoff_targets or []) if str(item).strip()]
    merged_handoffs = list(dict.fromkeys([*explicit_handoffs, *contract_handoffs]))
    return {
        "role": contract.get("role"),
        "scope": contract.get("scope"),
        "mutation_gate": contract.get("mutation_gate"),
        "reads": list(contract.get("reads", [])),
        "writes": list(contract.get("writes", [])),
        "will_not": list(contract.get("will_not", [])),
        "phase": phase,
        "manual_gate_required": manual_gate_required,
        "writes_applied": writes_applied,
        "next_owner": next_owner or (merged_handoffs[0] if merged_handoffs else skill_name),
        "handoff_targets": merged_handoffs,
        "blocked_writes": list(contract.get("will_not", [])),
        "summary": contract.get("summary"),
        "note": note,
    }
