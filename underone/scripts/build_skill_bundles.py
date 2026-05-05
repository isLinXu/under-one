#!/usr/bin/env python3
"""
build_skill_bundles.py — 从 underone/skills/{name}/ 构建 dist/{name}.skill 单文件包

.skill 文件格式：纯文本分发包，结构如下：

    ===== UNDER-ONE SKILL BUNDLE v1 =====
    name: {skill-name}
    version: {version}
    built_at: {iso_timestamp}
    files: {n}
    =====================================

    ----- file: SKILL.md -----
    <content>

    ----- file: scripts/foo.py -----
    <content>

    ===== END BUNDLE =====

用法：
    python scripts/build_skill_bundles.py              # 构建全部，输出到 ../dist/
    python scripts/build_skill_bundles.py bagua-zhen   # 构建单个
    python scripts/build_skill_bundles.py --check      # 只校验，不写
    python scripts/build_skill_bundles.py --out-dir .  # 输出到当前目录
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

SKILLS = [
    "bagua-zhen",
    "dalu-dongguan",
    "fenghou-qimen",
    "juling-qianjiang",
    "liuku-xianzei",
    "qiti-yuanliu",
    "shenji-bailian",
    "shuangquanshou",
    "tongtian-lu",
    "xiushen-lu",
]

VERSION = "v10.0.0"

BUNDLE_HEADER = "===== UNDER-ONE SKILL BUNDLE v1 ====="
BUNDLE_FOOTER = "===== END BUNDLE ====="
FILE_SEP_TPL = "----- file: {path} -----"

# 排除规则：不打包的文件/目录
EXCLUDE_DIRS = {"legacy", "__pycache__", "runtime_data", "backups"}
EXCLUDE_SUFFIXES = {".pyc", ".health_report.json"}


def iter_skill_files(skill_dir: Path) -> List[Tuple[str, Path]]:
    """返回 [(相对路径, 绝对路径), ...]，按字典序稳定排序。"""
    out: List[Tuple[str, Path]] = []
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file():
            continue
        # 跳过排除目录
        if any(part in EXCLUDE_DIRS for part in f.relative_to(skill_dir).parts):
            continue
        # 跳过排除后缀
        if any(f.name.endswith(suf) for suf in EXCLUDE_SUFFIXES):
            continue
        rel = f.relative_to(skill_dir).as_posix()
        out.append((rel, f))
    return out


def build_bundle(skill_name: str, repo_root: Path) -> str:
    skill_dir = repo_root / "underone" / "skills" / skill_name
    if not skill_dir.is_dir():
        raise FileNotFoundError(f"skill 目录不存在: {skill_dir}")

    files = iter_skill_files(skill_dir)
    if not files:
        raise RuntimeError(f"{skill_name} 没有可打包的文件")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines: List[str] = []
    lines.append(BUNDLE_HEADER)
    lines.append(f"name: {skill_name}")
    lines.append(f"version: {VERSION}")
    lines.append(f"built_at: {now}")
    lines.append(f"files: {len(files)}")
    lines.append("=" * len(BUNDLE_HEADER))
    lines.append("")

    for rel, path in files:
        lines.append("")
        lines.append(FILE_SEP_TPL.format(path=rel))
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # 二进制文件：跳过并记录
            lines.append("<binary file skipped>")
            continue
        lines.append(content.rstrip("\n"))

    lines.append("")
    lines.append(BUNDLE_FOOTER)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 .skill 单文件分发包")
    parser.add_argument("skill", nargs="?", help="指定 skill 名（不填则全部）")
    parser.add_argument(
        "--check", action="store_true", help="只校验，不写文件"
    )
    parser.add_argument(
        "--out-dir",
        default="../dist",
        help="输出目录（默认 ../dist/，相对于仓库根）",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    # out_dir 相对解析：绝对路径直接用；相对路径解析为 repo_root 下
    p = Path(args.out_dir)
    if p.is_absolute():
        out_dir = p
    elif args.out_dir.startswith(".."):
        # ../dist 表示希望写到 repo_root/dist
        out_dir = (repo_root / args.out_dir.lstrip("./").lstrip("../")).resolve()
    else:
        out_dir = (repo_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [args.skill] if args.skill else SKILLS
    unknown = [s for s in targets if s not in SKILLS]
    if unknown:
        print(f"ERROR: 未知 skill: {unknown}", file=sys.stderr)
        return 2

    ok = 0
    for name in targets:
        try:
            bundle = build_bundle(name, repo_root)
        except Exception as e:
            print(f"✗ {name}: {e}", file=sys.stderr)
            continue

        size_kb = len(bundle.encode("utf-8")) / 1024
        if args.check:
            print(f"✓ {name}: {size_kb:.1f} KB ({len(bundle.splitlines())} 行) [check only]")
        else:
            out_path = out_dir / f"{name}.skill"
            out_path.write_text(bundle, encoding="utf-8")
            try:
                display = out_path.relative_to(repo_root)
            except ValueError:
                display = out_path
            print(f"✓ {name} -> {display} ({size_kb:.1f} KB)")
        ok += 1

    print(f"\n完成: {ok}/{len(targets)} 个 skill 构建成功")
    return 0 if ok == len(targets) else 1


if __name__ == "__main__":
    sys.exit(main())
