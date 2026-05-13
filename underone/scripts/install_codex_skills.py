#!/usr/bin/env python3
"""Install under-one skills into Codex and validate each one independently."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "underone"))

from under_one.codex_skills import (
    DEFAULT_SKILLS,
    default_codex_skills_root,
    install_and_validate_codex_skill,
    iter_source_skill_dirs,
)


def _print_text_report(results, dest: Path) -> None:
    print(f"Codex skills target: {dest}")
    print("")
    for idx, item in enumerate(results, start=1):
        source_validation = item.get("source_validation") or {}
        scenario = source_validation.get("scenario") or {}
        install = item["install"]
        codex_validation = install["codex_validation"]
        lifecycle = install["installed_lifecycle"]
        print(f"[{idx}/{len(results)}] {item['skill']}")
        print(f"  installed_dir: {item['installed_dir']}")
        print(f"  codex_discovery: {'PASS' if codex_validation['passed'] else 'FAIL'}")
        print(f"  installed_self_test: {'PASS' if lifecycle['passed'] else 'FAIL'}")
        if source_validation:
            print(f"  source_validation: {'PASS' if source_validation['validation_passed'] else 'FAIL'}")
            if scenario:
                print(f"  effect: {scenario.get('effect_summary')}")
        if codex_validation["errors"]:
            print(f"  codex_errors: {codex_validation['errors']}")
        if codex_validation["warnings"]:
            print(f"  codex_warnings: {codex_validation['warnings']}")
        print(f"  overall: {'PASS' if item['overall_passed'] else 'FAIL'}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install under-one skills into Codex one by one.")
    parser.add_argument("skills", nargs="*", help="skill names to install; defaults to all")
    parser.add_argument("--dest", default=str(default_codex_skills_root()), help="Codex skills root")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON report")
    parser.add_argument("--no-force", action="store_true", help="do not overwrite existing installed skills")
    parser.add_argument(
        "--skip-source-validation",
        action="store_true",
        help="skip repo-side scenario validation and only verify the installed copy",
    )
    args = parser.parse_args()

    selected = args.skills or DEFAULT_SKILLS
    unknown = [name for name in selected if name not in DEFAULT_SKILLS]
    if unknown:
        print(f"ERROR: 未知 skill: {unknown}", file=sys.stderr)
        return 2

    dest = Path(args.dest).expanduser().resolve()
    source_root = REPO_ROOT / "underone" / "skills"

    results = []
    for skill_dir in iter_source_skill_dirs(source_root, selected):
        result = install_and_validate_codex_skill(
            skill_dir,
            target_root=dest,
            force=not args.no_force,
            include_source_validation=not args.skip_source_validation,
        )
        results.append(result)

    summary = {
        "target_root": str(dest),
        "skills_total": len(results),
        "skills_passed": sum(1 for item in results if item["overall_passed"]),
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_text_report(results, dest)
        print(f"summary: {summary['skills_passed']}/{summary['skills_total']} passed")
    return 0 if summary["skills_passed"] == summary["skills_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
