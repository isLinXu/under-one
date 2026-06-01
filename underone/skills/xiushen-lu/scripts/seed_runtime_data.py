#!/usr/bin/env python3
"""Deterministic runtime seeder for xiushen-lu bootstrap validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from metrics_collector import resolve_runtime_data_dir
except ImportError:
    def resolve_runtime_data_dir(data_dir=None) -> Path:
        return Path(data_dir or "runtime_data").expanduser()

from bootstrap_profiles import generate_profile_records, list_bootstrap_profiles


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic runtime traces for one or more under-one skills.",
    )
    parser.add_argument(
        "--skills",
        default="all",
        help="Comma-separated skill ids to seed. Use 'all' to seed every known profile.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=24,
        help="Number of records per skill. Default: 24",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260514,
        help="Deterministic seed used to derive per-skill traces.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to the resolved runtime_data directory.",
    )
    parser.add_argument(
        "--skills-dir",
        default=None,
        help="Optional skills root used to discover custom bootstrap profiles from _skillhub_meta.json.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def resolve_skill_selection(raw: str, skills_dir: str | None = None) -> List[str]:
    if raw.strip().lower() == "all":
        return list_bootstrap_profiles(skills_root=skills_dir)
    selected = [item.strip() for item in raw.split(",") if item.strip()]
    known = set(list_bootstrap_profiles(skills_root=skills_dir))
    unknown = [skill for skill in selected if skill not in known]
    if unknown:
        raise SystemExit(f"Unknown bootstrap profile(s): {', '.join(unknown)}")
    return selected


def write_seed_file(output_dir: Path, skill_name: str, records: List[dict]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{skill_name}_metrics.jsonl"
    with open(file_path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return file_path


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    skills = resolve_skill_selection(args.skills, skills_dir=args.skills_dir)
    output_dir = resolve_runtime_data_dir(args.output_dir)
    total = 0

    for skill_name in skills:
        skill_dir = None
        if args.skills_dir:
            skill_dir = Path(args.skills_dir).expanduser().resolve() / skill_name
        records = generate_profile_records(
            skill_name,
            n=args.count,
            seed=args.seed,
            skill_dir=skill_dir,
            skills_root=args.skills_dir,
        )
        target = write_seed_file(output_dir, skill_name, records)
        total += len(records)
        print(f"  Seeded {len(records)} records for {skill_name} -> {target}")

    print(
        f"\nOK: seeded {len(skills)} skill(s), {total} total records, seed={args.seed}, output_dir={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
