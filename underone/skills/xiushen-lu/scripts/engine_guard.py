#!/usr/bin/env python3
"""Runtime guards for xiushen-lu experimental engine entrypoints."""

from __future__ import annotations

import os
import sys
from typing import Iterable, List, Optional, Sequence

ALLOW_EXPERIMENTAL_ENTRY_ENV = "UNDERONE_ALLOW_XIUSHEN_EXPERIMENTS"
ALLOW_EXPERIMENTAL_ENTRY_FLAG = "--allow-experimental-entry"
TRUTHY_VALUES = {"1", "true", "yes", "on"}


def normalize_experimental_argv(argv: Optional[Sequence[str]] = None) -> List[str]:
    args = list(argv if argv is not None else sys.argv[1:])
    return [arg for arg in args if arg != ALLOW_EXPERIMENTAL_ENTRY_FLAG]


def experimental_entry_allowed(
    argv: Optional[Sequence[str]] = None,
    environ: Optional[dict] = None,
) -> bool:
    args = list(argv if argv is not None else sys.argv[1:])
    if ALLOW_EXPERIMENTAL_ENTRY_FLAG in args:
        return True
    env = environ if environ is not None else os.environ
    raw = str(env.get(ALLOW_EXPERIMENTAL_ENTRY_ENV, "")).strip().lower()
    return raw in TRUTHY_VALUES


def build_deprecated_entry_message(
    engine_name: str,
    replaced_by: str,
    note: str,
) -> str:
    lines = [
        f"[xiushen-lu] {engine_name} 是实验性引擎，默认不作为生产入口运行。",
        f"[xiushen-lu] 请改用: python {replaced_by} <skills_dir> [skill_name] [--apply]",
        f"[xiushen-lu] 说明: {note}",
        (
            f"[xiushen-lu] 如需显式运行实验原型，请传入 "
            f"`{ALLOW_EXPERIMENTAL_ENTRY_FLAG}` 或设置环境变量 "
            f"`{ALLOW_EXPERIMENTAL_ENTRY_ENV}=1`。"
        ),
    ]
    return "\n".join(lines)


def enforce_deprecated_entry_guard(
    engine_name: str,
    replaced_by: str,
    note: str,
    argv: Optional[Sequence[str]] = None,
    environ: Optional[dict] = None,
) -> List[str]:
    if experimental_entry_allowed(argv=argv, environ=environ):
        return normalize_experimental_argv(argv=argv)

    print(build_deprecated_entry_message(engine_name, replaced_by, note), file=sys.stderr)
    raise SystemExit(2)


__all__ = [
    "ALLOW_EXPERIMENTAL_ENTRY_ENV",
    "ALLOW_EXPERIMENTAL_ENTRY_FLAG",
    "build_deprecated_entry_message",
    "enforce_deprecated_entry_guard",
    "experimental_entry_allowed",
    "normalize_experimental_argv",
]
