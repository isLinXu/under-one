#!/usr/bin/env python3
"""Deterministic bootstrap profiles for under-one skills.

This module gives xiushen-lu a reusable cold-start baseline:
- `get_bootstrap_profile()` returns the expected operating envelope per skill.
- `generate_profile_records()` emits deterministic seed metrics for isolated tests.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parent.parent.parent
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

try:
    from _skill_config import get_skill_config
except ImportError:
    def get_skill_config(_skill_name: str, _key: str = None, default=None):
        return default


BOOTSTRAP_PROFILES: Dict[str, Dict[str, float]] = {
    "qiti-yuanliu": {
        "avg_quality": 92.0,
        "avg_completeness": 95.0,
        "avg_consistency": 94.0,
        "avg_human": 0.02,
        "success_rate": 0.98,
        "avg_duration": 520.0,
        "recommended_min_records": 12,
        "degradation_window": 4,
    },
    "tongtian-lu": {
        "avg_quality": 91.0,
        "avg_completeness": 93.0,
        "avg_consistency": 90.0,
        "avg_human": 0.02,
        "success_rate": 0.96,
        "avg_duration": 760.0,
        "recommended_min_records": 10,
        "degradation_window": 4,
    },
    "dalu-dongguan": {
        "avg_quality": 88.0,
        "avg_completeness": 91.0,
        "avg_consistency": 89.0,
        "avg_human": 0.05,
        "success_rate": 0.94,
        "avg_duration": 700.0,
        "recommended_min_records": 10,
        "degradation_window": 4,
    },
    "shenji-bailian": {
        "avg_quality": 95.0,
        "avg_completeness": 96.0,
        "avg_consistency": 93.0,
        "avg_human": 0.01,
        "success_rate": 0.97,
        "avg_duration": 1180.0,
        "recommended_min_records": 8,
        "degradation_window": 3,
    },
    "fenghou-qimen": {
        "avg_quality": 95.0,
        "avg_completeness": 95.0,
        "avg_consistency": 94.0,
        "avg_human": 0.01,
        "success_rate": 0.98,
        "avg_duration": 540.0,
        "recommended_min_records": 8,
        "degradation_window": 3,
    },
    "liuku-xianzei": {
        "avg_quality": 84.0,
        "avg_completeness": 88.0,
        "avg_consistency": 83.0,
        "avg_human": 0.07,
        "success_rate": 0.91,
        "avg_duration": 980.0,
        "recommended_min_records": 12,
        "degradation_window": 5,
    },
    "shuangquanshou": {
        "avg_quality": 90.0,
        "avg_completeness": 92.0,
        "avg_consistency": 94.0,
        "avg_human": 0.04,
        "success_rate": 0.93,
        "avg_duration": 500.0,
        "recommended_min_records": 10,
        "degradation_window": 4,
    },
    "juling-qianjiang": {
        "avg_quality": 92.0,
        "avg_completeness": 93.0,
        "avg_consistency": 89.0,
        "avg_human": 0.03,
        "success_rate": 0.95,
        "avg_duration": 1100.0,
        "recommended_min_records": 12,
        "degradation_window": 4,
    },
    "bagua-zhen": {
        "avg_quality": 96.0,
        "avg_completeness": 96.0,
        "avg_consistency": 95.0,
        "avg_human": 0.0,
        "success_rate": 0.99,
        "avg_duration": 420.0,
        "recommended_min_records": 8,
        "degradation_window": 3,
    },
    "xiushen-lu": {
        "avg_quality": 90.0,
        "avg_completeness": 94.0,
        "avg_consistency": 88.0,
        "avg_human": 0.02,
        "success_rate": 0.96,
        "avg_duration": 820.0,
        "recommended_min_records": 12,
        "degradation_window": 4,
    },
}

PROFILE_FIELDS = {
    "avg_quality",
    "avg_completeness",
    "avg_consistency",
    "avg_human",
    "success_rate",
    "avg_duration",
    "recommended_min_records",
    "degradation_window",
}


def _normalize_profile(profile: Any) -> Optional[Dict[str, float]]:
    if not isinstance(profile, dict):
        return None
    normalized: Dict[str, float] = {}
    for key in PROFILE_FIELDS:
        value = profile.get(key)
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if key in {"recommended_min_records", "degradation_window"}:
            normalized[key] = int(round(number))
        else:
            normalized[key] = number
    return normalized or None


def _merge_profile(base: Optional[Dict[str, float]], override: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
    if not base and not override:
        return None
    merged: Dict[str, float] = {}
    if base:
        merged.update(base)
    if override:
        merged.update(override)
    return merged


def _load_json_object(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _discover_skill_dir(
    skill_name: str,
    skill_dir: Optional[Path | str] = None,
    skills_root: Optional[Path | str] = None,
) -> Optional[Path]:
    if skill_dir:
        candidate = Path(skill_dir).expanduser().resolve()
        if candidate.exists():
            return candidate
    root = Path(skills_root).expanduser().resolve() if skills_root else SKILLS_ROOT
    candidate = root / skill_name
    return candidate if candidate.exists() else None


def _load_meta_profile(
    skill_name: str,
    skill_dir: Optional[Path | str] = None,
    skills_root: Optional[Path | str] = None,
) -> Optional[Dict[str, float]]:
    resolved_dir = _discover_skill_dir(skill_name, skill_dir=skill_dir, skills_root=skills_root)
    if not resolved_dir:
        return None
    meta_path = resolved_dir / "_skillhub_meta.json"
    if not meta_path.exists():
        return None
    payload = _load_json_object(meta_path)
    return _normalize_profile(payload.get("bootstrap_profile"))


def _load_config_profiles() -> Dict[str, Dict[str, float]]:
    merged: Dict[str, Dict[str, float]] = {}

    raw_inline = get_skill_config("xiushenlu", "bootstrap_profiles", {}) or {}
    if isinstance(raw_inline, dict):
        for skill_name, profile in raw_inline.items():
            normalized = _normalize_profile(profile)
            if normalized:
                merged[str(skill_name)] = normalized

    profiles_path = get_skill_config("xiushenlu", "bootstrap_profiles_path", None)
    if profiles_path:
        path = Path(str(profiles_path)).expanduser()
        if path.exists():
            payload = _load_json_object(path)
            for skill_name, profile in payload.items():
                normalized = _normalize_profile(profile)
                if normalized:
                    merged[str(skill_name)] = normalized
    return merged


def list_bootstrap_profiles(skills_root: Optional[Path | str] = None) -> List[str]:
    names = set(BOOTSTRAP_PROFILES)
    names.update(_load_config_profiles())

    root = Path(skills_root).expanduser().resolve() if skills_root else SKILLS_ROOT
    if root.exists():
        for skill_dir in root.iterdir():
            if not skill_dir.is_dir():
                continue
            meta_path = skill_dir / "_skillhub_meta.json"
            if not meta_path.exists():
                continue
            payload = _load_json_object(meta_path)
            if _normalize_profile(payload.get("bootstrap_profile")):
                names.add(skill_dir.name)
    return sorted(names)


def get_bootstrap_profile(
    skill_name: str,
    skill_dir: Optional[Path | str] = None,
    skills_root: Optional[Path | str] = None,
) -> Optional[Dict[str, float]]:
    profile = deepcopy(BOOTSTRAP_PROFILES.get(skill_name))
    profile = _merge_profile(profile, _load_config_profiles().get(skill_name))
    profile = _merge_profile(profile, _load_meta_profile(skill_name, skill_dir=skill_dir, skills_root=skills_root))
    return profile


def _skill_seed(skill_name: str, seed: int) -> int:
    return seed + sum((idx + 1) * ord(ch) for idx, ch in enumerate(skill_name))


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def generate_profile_records(
    skill_name: str,
    n: int = 24,
    seed: int = 20260514,
    start_time: Optional[datetime] = None,
    skill_dir: Optional[Path | str] = None,
    skills_root: Optional[Path | str] = None,
) -> List[Dict[str, object]]:
    profile = get_bootstrap_profile(skill_name, skill_dir=skill_dir, skills_root=skills_root)
    if not profile:
        raise ValueError(f"Unknown bootstrap profile: {skill_name}")
    if n <= 0:
        return []

    rng = random.Random(_skill_seed(skill_name, seed))
    base_time = start_time or datetime(2026, 5, 6, 8, 0, 0)
    tail = max(2, min(int(profile.get("degradation_window", 4)), max(2, n // 4)))
    records: List[Dict[str, object]] = []

    for idx in range(n):
        in_tail = idx >= n - tail
        quality = float(profile["avg_quality"]) + rng.uniform(-3.5, 3.5)
        completeness = float(profile["avg_completeness"]) + rng.uniform(-3.0, 2.0)
        consistency = float(profile["avg_consistency"]) + rng.uniform(-3.0, 2.5)
        human = float(profile["avg_human"]) + rng.uniform(-0.01, 0.03)
        success_rate = float(profile["success_rate"])
        errors = rng.uniform(0.0, 0.08)

        if in_tail:
            quality -= rng.uniform(4.0, 9.0)
            completeness -= rng.uniform(2.0, 6.0)
            consistency -= rng.uniform(3.0, 8.0)
            human += rng.uniform(0.03, 0.10)
            success_rate *= 0.88
            errors += rng.uniform(0.04, 0.16)

        quality = round(_bounded(quality, 45.0, 99.0), 1)
        completeness = round(_bounded(completeness, 60.0, 100.0), 1)
        consistency = round(_bounded(consistency, 55.0, 100.0), 1)
        human = round(_bounded(human, 0.0, 1.0), 2)
        duration_ms = round(
            _bounded(float(profile["avg_duration"]) + rng.uniform(-90.0, 140.0), 80.0, 5000.0),
            1,
        )
        success = rng.random() < success_rate

        records.append(
            {
                "skill_name": skill_name,
                "timestamp": (base_time + timedelta(minutes=idx * 30)).isoformat(),
                "duration_ms": duration_ms,
                "success": success,
                "quality_score": quality,
                "error_count": round(_bounded(errors, 0.0, 3.0), 2),
                "human_intervention": human,
                "output_completeness": completeness,
                "consistency_score": consistency,
            }
        )

    return records
