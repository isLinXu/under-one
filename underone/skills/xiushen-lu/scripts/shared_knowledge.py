#!/usr/bin/env python3
"""Compatibility shim for xiushen-lu shared knowledge imports.

This module keeps the historical import path
`xiushen-lu/scripts/shared_knowledge.py` alive.

Behavior:
- In the source repository, it forwards to the canonical shared hub at
  `underone/skills/shared_knowledge.py`.
- In standalone bundle installs, it falls back to a local implementation so
  `skillctl self-test` remains self-contained.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ENGINE_STATUS = "compatibility-shim"
DEPRECATED = True
REPLACED_BY = "../../shared_knowledge.py"


def _candidate_canonical_paths() -> List[Path]:
    current = Path(__file__).resolve()
    return [
        current.parents[2] / "shared_knowledge.py",
        current.parents[1] / "shared_knowledge.py",
        current.parent / "_shared_knowledge.py",
    ]


def _load_canonical_module():
    current = Path(__file__).resolve()
    for candidate in _candidate_canonical_paths():
        if candidate == current or not candidate.exists() or candidate.is_dir():
            continue
        spec = importlib.util.spec_from_file_location("_underone_shared_knowledge", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return None


_MODULE = _load_canonical_module()

if _MODULE is not None:
    KnowledgeHub = _MODULE.KnowledgeHub
    get_hub = _MODULE.get_hub
else:
    try:
        from metrics_collector import resolve_runtime_data_dir
    except ImportError:
        def resolve_runtime_data_dir(data_dir=None) -> Path:
            return Path(data_dir or "runtime_data").expanduser()

    _knowledge_hub_instance = None
    _knowledge_hub_dir: Optional[Path] = None

    class KnowledgeHub:
        """Local fallback for standalone bundle installs."""

        def __init__(self, data_dir: Optional[str] = None):
            self.data_dir = resolve_runtime_data_dir(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.knowledge_file = self.data_dir / "shared_knowledge.json"
            self._knowledge: Dict[str, List[Dict[str, Any]]] = self._load()

        def _load(self) -> Dict[str, List[Dict[str, Any]]]:
            if not self.knowledge_file.exists():
                return {}
            try:
                return json.loads(self.knowledge_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}

        def _save(self) -> None:
            self.knowledge_file.write_text(
                json.dumps(self._knowledge, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        def contribute(self, skill_name: str, knowledge_type: str, data: Dict[str, Any]) -> None:
            key = f"{skill_name}:{knowledge_type}"
            entry = {
                "timestamp": datetime.now().isoformat(),
                "skill_name": skill_name,
                "type": knowledge_type,
                "data": data,
            }
            self._knowledge.setdefault(key, []).append(entry)
            self._knowledge[key] = self._knowledge[key][-50:]
            self._save()

        def query(self, knowledge_type: str, skill_name: Optional[str] = None, n: int = 5) -> List[Dict[str, Any]]:
            results: List[Dict[str, Any]] = []
            for key, entries in self._knowledge.items():
                entry_skill, _, entry_type = key.partition(":")
                if entry_type != knowledge_type:
                    continue
                if skill_name is not None and entry_skill != skill_name:
                    continue
                results.extend(entries)
            results.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
            return results[:n]

        def get_threshold(self, skill_name: str, key: str) -> Optional[float]:
            entries = self.query("threshold_evolution", skill_name=skill_name, n=1)
            if not entries:
                return None
            change = str(entries[0].get("data", {}).get("change", ""))
            import re
            match = re.search(r"([\d.]+)", change)
            if match:
                return float(match.group(1))
            return None

        def get_similar_skills(self, skill_name: str) -> List[str]:
            similarity_map = {
                "qiti-yuanliu": ["shuangquanshou"],
                "tongtian-lu": ["shenji-bailian"],
                "fenghou-qimen": ["juling-qianjiang"],
                "liuku-xianzei": ["dalu-dongguan"],
            }
            return similarity_map.get(skill_name, [])

        def stats(self) -> Dict[str, Any]:
            total_entries = sum(len(items) for items in self._knowledge.values())
            return {
                "total_entries": total_entries,
                "categories": list(self._knowledge.keys()),
                "file": str(self.knowledge_file),
            }

    def get_hub(data_dir: Optional[str] = None) -> KnowledgeHub:
        global _knowledge_hub_instance, _knowledge_hub_dir
        resolved_dir = resolve_runtime_data_dir(data_dir)
        if _knowledge_hub_instance is None or _knowledge_hub_dir != resolved_dir:
            _knowledge_hub_instance = KnowledgeHub(str(resolved_dir))
            _knowledge_hub_dir = resolved_dir
        return _knowledge_hub_instance


sys.modules.setdefault("shared_knowledge", sys.modules[__name__])

__all__ = [
    "KnowledgeHub",
    "get_hub",
    "ENGINE_STATUS",
    "DEPRECATED",
    "REPLACED_BY",
]
