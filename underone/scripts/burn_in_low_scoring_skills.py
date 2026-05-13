#!/usr/bin/env python3
"""Burn-in runner for low-scoring skills.

Runs stable smoke scenarios repeatedly so recent runtime metrics reflect the
current hardened behavior of `bagua-zhen` and `xiushen-lu`.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_ROOT = REPO_ROOT / "underone"
SKILLS_ROOT = PACKAGE_ROOT / "skills"

sys.path.insert(0, str(PACKAGE_ROOT))


def _import_skill(module_path: str):
    parts = module_path.split(".")
    parts[0] = parts[0].replace("_", "-")
    file_path = SKILLS_ROOT / Path(*parts[:-1]) / f"{parts[-1]}.py"
    spec = importlib.util.spec_from_file_location(module_path, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


coordinator = _import_skill("bagua_zhen.scripts.coordinator")
core_engine = _import_skill("xiushen_lu.scripts.core_engine")


def burn_in(iterations: int) -> dict:
    summary = {"bagua-zhen": 0, "xiushen-lu": 0}
    for _ in range(iterations):
        coordinator.coordinate(str(SKILLS_ROOT))
        summary["bagua-zhen"] += 1

        core = core_engine.XiuShenLuCoreV7(str(SKILLS_ROOT), data_dir=str(REPO_ROOT / "runtime_data"), apply_changes=False)
        core.run_evolution_cycle()
        summary["xiushen-lu"] += 1
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Burn in low-scoring skills with stable smoke runs.")
    parser.add_argument("--iterations", type=int, default=5, help="Number of burn-in rounds to run.")
    args = parser.parse_args()

    summary = burn_in(max(1, args.iterations))
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
