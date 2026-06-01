"""Robust resolution of the ``skills/`` directory.

Historically both :mod:`under_one` and :mod:`under_one.cli` carried their own
copy of a skill-directory finder that walked a list of hard-coded candidate
paths and probed for a single ``qiti-yuanliu`` directory. That heuristic was
fragile: it offered no explicit override, gave an opaque error on failure, and
could be fooled by an unrelated directory that happened to contain a
``qiti-yuanliu`` folder.

This module centralises that logic so every caller shares one well-tested,
overridable implementation.

Resolution order:

1. ``UNDER_ONE_SKILLS_DIR`` environment variable (highest priority). The value
   may point at the ``skills/`` directory directly or at its parent (e.g. the
   ``underone/`` package root).
2. The ``skills/`` directory shipped next to this package.
3. Common working-directory layouts (repo root, ``underone/``).
4. A global install at ``~/.under-one/skills``.

A directory only qualifies as a skills root when it contains the control-plane
skills (``qiti-yuanliu``/``bagua-zhen``/``xiushen-lu``), which makes false
positives effectively impossible.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

from .exceptions import SkillExecutionError

#: Environment variable callers can set to force a specific skills directory.
SKILLS_DIR_ENV = "UNDER_ONE_SKILLS_DIR"

#: Control-plane skills that must all be present for a directory to count as a
#: valid skills root. Using more than one marker avoids accidental matches.
_REQUIRED_MARKERS = ("qiti-yuanliu", "bagua-zhen", "xiushen-lu")


def looks_like_skills_root(path: Path) -> bool:
    """Return ``True`` when *path* contains the control-plane skill directories."""

    try:
        return all((path / marker).is_dir() for marker in _REQUIRED_MARKERS)
    except OSError:
        return False


def _default_candidates() -> List[Path]:
    package_skills = Path(__file__).resolve().parent.parent / "skills"
    cwd = Path.cwd()
    return [
        package_skills,
        cwd / "underone" / "skills",
        cwd / "skills",
        cwd,
        Path.home() / ".under-one" / "skills",
    ]


def _env_candidates() -> List[Path]:
    raw = os.getenv(SKILLS_DIR_ENV)
    if not raw:
        return []
    base = Path(raw).expanduser()
    # Accept either the skills directory itself or a parent that holds it.
    return [base, base / "skills"]


def find_skills_dir(extra_candidates: Optional[Iterable[Path]] = None) -> Path:
    """Locate the ``skills/`` directory.

    Args:
        extra_candidates: Optional additional directories to try before the
            built-in defaults (after the environment override).

    Returns:
        The resolved skills directory.

    Raises:
        SkillExecutionError: When no candidate directory looks like a valid
            skills root. The message lists every path that was inspected so the
            failure is diagnosable.
    """

    searched: List[Path] = []
    candidates: List[Path] = []
    candidates.extend(_env_candidates())
    if extra_candidates:
        candidates.extend(Path(c) for c in extra_candidates)
    candidates.extend(_default_candidates())

    for candidate in candidates:
        if candidate in searched:
            continue
        searched.append(candidate)
        if looks_like_skills_root(candidate):
            return candidate

    searched_list = "\n  - ".join(str(path) for path in searched)
    raise SkillExecutionError(
        "locator",
        "找不到 skills 目录。已搜索以下路径：\n  - "
        + searched_list
        + f"\n请通过环境变量 {SKILLS_DIR_ENV} 显式指定 skills 目录，"
        + "或在 under-one 仓库内运行，或执行 `pip install -e underone/`。",
    )
