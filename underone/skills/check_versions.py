#!/usr/bin/env python3
"""
版本号检查脚本

检查所有 skill 的 `SKILL.md` 与 `_skillhub_meta.json` 当前版本是否一致。
当 metadata 缺失时，才回退到主脚本中的历史版本注释做辅助检查。

用法:
    python check_versions.py                # 检查所有 skill
    python check_versions.py dalu-dongguan  # 检查指定 skill
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

SKILLS_ROOT = Path(__file__).resolve().parent
VERSION_PATTERN = re.compile(r'version\s*:\s*["\']?(v?\d+\.\d+\.\d+)["\']?', re.IGNORECASE)
SCRIPT_VERSION_PATTERN = re.compile(r'[Vv](\d+\.\d+(?:\.\d+)?)')
SCRIPT_CURRENT_VERSION_PATTERNS = [
    re.compile(r'VERSION\s*=\s*["\'](v?\d+\.\d+\.\d+)["\']'),
    re.compile(r'"version"\s*:\s*["\'](v?\d+\.\d+\.\d+)["\']'),
]


def extract_skill_md_version(skill_path: Path) -> Optional[str]:
    """从SKILL.md的metadata中提取version"""
    md_file = skill_path / "SKILL.md"
    if not md_file.exists():
        return None

    content = md_file.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(content)
    return match.group(1) if match else None


def extract_meta_version(skill_path: Path) -> Optional[str]:
    """从 _skillhub_meta.json 中提取当前版本。"""
    meta_file = skill_path / "_skillhub_meta.json"
    if not meta_file.exists():
        return None
    try:
        payload = json.loads(meta_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    version = payload.get("version")
    return str(version) if version is not None else None


def extract_script_version(skill_path: Path) -> Optional[str]:
    """从主脚本中提取版本号（仅作为 metadata 缺失时的辅助信息）"""
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return None

    scripts = sorted(scripts_dir.glob("*.py"))
    if not scripts:
        return None

    entry_rel = None
    meta_file = skill_path / "_skillhub_meta.json"
    if meta_file.exists():
        try:
            payload = json.loads(meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            entry_rel = payload.get("entry")

    main_script = None
    if isinstance(entry_rel, str) and entry_rel.strip():
        candidate = skill_path / Path(entry_rel)
        if candidate.exists():
            main_script = candidate

    if main_script is None:
        skill_name = skill_path.name
        candidate = scripts_dir / f"{skill_name.replace('-', '_')}.py"
        main_script = candidate if candidate.exists() else scripts[0]

    content = main_script.read_text(encoding="utf-8")
    for pattern in SCRIPT_CURRENT_VERSION_PATTERNS:
        match = pattern.search(content)
        if match:
            return match.group(1)
    match = SCRIPT_VERSION_PATTERN.search(content)
    return f"v{match.group(1)}" if match else None


def check_skill(skill_name: str) -> dict:
    """检查单个skill的版本一致性"""
    skill_path = SKILLS_ROOT / skill_name

    result = {
        "skill": skill_name,
        "md_version": None,
        "meta_version": None,
        "script_version": None,
        "match": None,
        "error": None,
    }

    if not skill_path.exists():
        result["error"] = "Skill目录不存在"
        return result

    md_version = extract_skill_md_version(skill_path)
    meta_version = extract_meta_version(skill_path)
    script_version = extract_script_version(skill_path)

    result["md_version"] = md_version
    result["meta_version"] = meta_version
    result["script_version"] = script_version

    if md_version and meta_version:
        result["match"] = (md_version == meta_version)
        if result["match"] is False:
            result["error"] = f"SKILL.md={md_version}, _skillhub_meta.json={meta_version}"
    elif md_version and script_version:
        result["match"] = (md_version == script_version)
        if result["match"] is False:
            result["error"] = f"SKILL.md={md_version}, script={script_version}"
    elif meta_version and not md_version:
        result["match"] = None
        result["error"] = "SKILL.md中未找到版本号"
    elif md_version and not meta_version and not script_version:
        result["match"] = None
        result["error"] = "metadata和脚本中均未找到版本号"
    else:
        result["match"] = None
        result["error"] = "缺少可比较的版本信息"

    return result


def check_all_skills() -> list:
    """检查所有skill"""
    results = []
    for skill_path in SKILLS_ROOT.iterdir():
        if not skill_path.is_dir() or skill_path.name.startswith("_"):
            continue
        if not (skill_path / "SKILL.md").exists():
            continue
        result = check_skill(skill_path.name)
        results.append(result)
    return results


def main():
    if len(sys.argv) > 1:
        # 检查指定skill
        skill_name = sys.argv[1]
        result = check_skill(skill_name)
        print(f"=== {skill_name} 版本检查 ===")
        print(f"SKILL.md版本: {result['md_version']}")
        print(f"metadata版本: {result['meta_version']}")
        print(f"脚本版本: {result['script_version']}")
        if result["match"] is True:
            print("✅ 版本一致")
        elif result["match"] is False:
            print(f"❌ 版本不一致！ SKILL.md={result['md_version']}, 脚本={result['script_version']}")
            sys.exit(1)
        else:
            print(f"⚠️  {result.get('error', '无法比较')}")
    else:
        # 检查所有skill
        results = check_all_skills()
        print("=" * 60)
        print("版本号检查报告")
        print("=" * 60)

        all_pass = True
        has_issues = False

        for r in sorted(results, key=lambda x: x["skill"]):
            status = "✅" if r["match"] is True else ("❌" if r["match"] is False else "⚠️")
            md = r["md_version"] or "?"
            meta = r["meta_version"] or "?"
            sc = r["script_version"] or "?"
            error = f" [{r.get('error', '')}]" if r.get("error") else ""
            print(f"{status} {r['skill']:<20} md={md:<10} meta={meta:<10} script={sc:<10}{error}")

            if r["match"] is False:
                all_pass = False
            elif r["match"] is None:
                has_issues = True

        print("=" * 60)
        if all_pass:
            print("✅ 所有skill版本号一致")
        elif has_issues:
            print("⚠️ 部分skill存在版本信息问题")
            sys.exit(2)
        else:
            print("❌ 存在版本不一致的skill")
            sys.exit(1)


if __name__ == "__main__":
    main()
