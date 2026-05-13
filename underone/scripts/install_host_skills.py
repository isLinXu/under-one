#!/usr/bin/env python3
"""Install under-one skills into a supported host runtime and validate each one independently."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "underone"))

from under_one.hosted_skills import (
    DEFAULT_SKILLS,
    available_hosts,
    default_host_skills_root,
    get_host_profile,
    install_and_validate_host_skill,
    iter_source_skill_dirs,
)


def _print_text_report(results, dest: Path, host: str) -> None:
    profile = get_host_profile(host)
    print(f"{profile.label} skills target: {dest}")
    print("")
    for idx, item in enumerate(results, start=1):
        source_validation = item.get("source_validation") or {}
        scenario = source_validation.get("scenario") or {}
        install = item["install"]
        host_validation = install["host_validation"]
        lifecycle = install["installed_lifecycle"]
        print(f"[{idx}/{len(results)}] {item['skill']}")
        print(f"  installed_dir: {item['installed_dir']}")
        print(f"  {profile.name}_discovery: {'PASS' if host_validation['passed'] else 'FAIL'}")
        print(f"  installed_self_test: {'PASS' if lifecycle['passed'] else 'FAIL'}")
        if source_validation:
            print(f"  source_validation: {'PASS' if source_validation['validation_passed'] else 'FAIL'}")
            if scenario:
                print(f"  effect: {scenario.get('effect_summary')}")
        if host_validation["errors"]:
            print(f"  {profile.name}_errors: {host_validation['errors']}")
        if host_validation["warnings"]:
            print(f"  {profile.name}_warnings: {host_validation['warnings']}")
        print(f"  overall: {'PASS' if item['overall_passed'] else 'FAIL'}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install under-one skills into a supported host runtime.")
    parser.add_argument("skills", nargs="*", help="skill names to install; defaults to all")
    parser.add_argument("--host", choices=available_hosts(), default="codex", help="target host runtime")
    parser.add_argument("--dest", help="host skills root (defaults to the host's standard directory)")
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

    dest = Path(args.dest).expanduser().resolve() if args.dest else default_host_skills_root(args.host).resolve()
    source_root = REPO_ROOT / "underone" / "skills"

    results = []
    for skill_dir in iter_source_skill_dirs(source_root, selected):
        result = install_and_validate_host_skill(
            skill_dir,
            args.host,
            target_root=dest,
            force=not args.no_force,
            include_source_validation=not args.skip_source_validation,
        )
        results.append(result)

    summary = {
        "host": get_host_profile(args.host).name,
        "target_root": str(dest),
        "skills_total": len(results),
        "skills_passed": sum(1 for item in results if item["overall_passed"]),
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_text_report(results, dest, args.host)
        print(f"summary: {summary['skills_passed']}/{summary['skills_total']} passed")
    return 0 if summary["skills_passed"] == summary["skills_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
