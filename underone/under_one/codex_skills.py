"""Codex-compatible installation helpers for under-one skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from .hosted_skills import (
    DEFAULT_SKILLS,
    build_codex_skill_markdown,
    build_openai_yaml,
    default_codex_skills_root,
    install_and_validate_codex_skill,
    install_codex_skill,
    iter_source_skill_dirs,
    verify_codex_skill_install,
)

__all__ = [
    "DEFAULT_SKILLS",
    "build_codex_skill_markdown",
    "build_openai_yaml",
    "default_codex_skills_root",
    "install_and_validate_codex_skill",
    "install_codex_skill",
    "iter_source_skill_dirs",
    "verify_codex_skill_install",
]
