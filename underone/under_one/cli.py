#!/usr/bin/env python3
"""
under-one.skills 统一CLI入口

Usage:
    under-one --help
    under-one list                       # 列出所有可用skill
    under-one scan <skill> <input>       # 运行指定skill
    under-one status                     # 查看十技生态状态
    under-one evolve [skill]             # 启动修身炉进化
    under-one bundles [--check] [skill]  # 构建 .skill 单文件分发包
    under-one providers                  # 列出可用 LLM 适配器
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

SKILL_MAP = {
    "context-guard":      ("qiti-yuanliu",       "scripts/entropy_scanner.py",   "上下文稳态扫描"),
    "command-factory":    ("tongtian-lu",        "scripts/fu_generator.py",      "指令拆解"),
    "insight-radar":      ("dalu-dongguan",      "scripts/link_detector.py",     "全局洞察"),
    "tool-forge":         ("shenji-bailian",     "scripts/tool_factory.py",      "工具锻造"),
    "priority-engine":    ("fenghou-qimen",      "scripts/priority_engine.py",   "优先级排序"),
    "knowledge-digest":   ("liuku-xianzei",      "scripts/knowledge_digest.py",  "知识消化"),
    "persona-guard":      ("shuangquanshou",     "scripts/dna_validator.py",     "人格守护"),
    "tool-orchestrator":  ("juling-qianjiang",   "scripts/dispatcher.py",        "工具调度"),
    "ecosystem-hub":      ("bagua-zhen",         "scripts/coordinator.py",       "生态监控"),
    "evolution-engine":   ("xiushen-lu",         "scripts/core_engine.py",       "自进化"),
}


def find_skill_dir() -> Path:
    """查找 skills 目录（underone/skills/）"""
    candidates = [
        # Python 包位于 underone/under_one/，skills 位于 underone/skills/
        Path(__file__).parent.parent / "skills",
        # 兼容：从 repo 根或其他上下文运行
        Path.cwd() / "underone" / "skills",
        Path.cwd() / "skills",
        Path.cwd(),
        Path.home() / ".under-one/skills",
    ]
    for c in candidates:
        if (c / "qiti-yuanliu").exists():
            return c
    print("ERROR: 找不到 skills 目录。请确保在 under-one 仓库内运行，或 pip install -e underone/")
    sys.exit(1)


def cmd_list(args):
    """列出所有可用skill"""
    print(f"\n{'Skill Name':<20} {'目录':<20} {'中文名（彩蛋）':<15} {'描述'}")
    print("-" * 70)
    for name, (dir_name, _, desc) in SKILL_MAP.items():
        cn = {
            "context-guard": "炁体源流", "command-factory": "通天箓",
            "insight-radar": "大罗洞观", "tool-forge": "神机百炼",
            "priority-engine": "风后奇门", "knowledge-digest": "六库仙贼",
            "persona-guard": "双全手", "tool-orchestrator": "拘灵遣将",
            "ecosystem-hub": "八卦阵", "evolution-engine": "修身炉",
        }.get(name, "")
        print(f"{name:<20} {dir_name:<20} {cn:<15} {desc}")
    print(f"\n共 {len(SKILL_MAP)} 个skill可用")


def cmd_scan(args):
    """运行指定skill"""
    skill_name = args.skill
    
    if skill_name not in SKILL_MAP:
        print(f"ERROR: 未知skill '{skill_name}'。运行 'under-one list' 查看可用skill。")
        sys.exit(1)
    
    dir_name, script_name, desc = SKILL_MAP[skill_name]
    skill_dir = find_skill_dir() / dir_name
    script_path = skill_dir / script_name
    
    if not script_path.exists():
        print(f"ERROR: 脚本不存在: {script_path}")
        sys.exit(1)
    
    import subprocess
    cmd = ["python", str(script_path)]
    if args.input:
        cmd.append(args.input)
    
    print(f"[{skill_name}] {desc}")
    print(f"脚本: {script_path}")
    if args.input:
        print(f"输入: {args.input}")
    print("-" * 40)
    
    result = subprocess.run(cmd, timeout=60)
    sys.exit(result.returncode)


def cmd_status(args):
    """查看十技生态状态"""
    skill_dir = find_skill_dir()
    coord_script = skill_dir / "bagua-zhen/scripts/coordinator.py"
    
    if coord_script.exists():
        import subprocess
        subprocess.run(["python", str(coord_script)])
    else:
        # Fallback: 简单扫描
        print("\n☯ 十技生态状态 (简化版)")
        print("-" * 40)
        for name, (dir_name, _, desc) in SKILL_MAP.items():
            metrics_file = Path("runtime_data") / f"{dir_name}_metrics.jsonl"
            count = 0
            if metrics_file.exists():
                with open(metrics_file) as f:
                    count = sum(1 for _ in f if _.strip())
            status = f"活跃({count}次)" if count > 0 else "休眠"
            print(f"  {name:<20} {status}")


def cmd_evolve(args):
    """启动修身炉进化"""
    skill_dir = find_skill_dir()
    engine_script = skill_dir / "xiushen-lu/scripts/core_engine.py"
    
    if not engine_script.exists():
        print("ERROR: 修身炉引擎不存在")
        sys.exit(1)
    
    import subprocess
    cmd = ["python", str(engine_script), str(skill_dir)]
    if args.skill:
        cmd.append(args.skill)
    
    print("🔥 启动修身炉自进化...")
    subprocess.run(cmd, timeout=300)


def cmd_bundles(args):
    """构建 .skill 单文件分发包"""
    skill_dir = find_skill_dir()
    builder = skill_dir / "scripts" / "build_skill_bundles.py"
    if not builder.exists():
        print("ERROR: 找不到 scripts/build_skill_bundles.py")
        sys.exit(1)
    import subprocess

    cmd = ["python", str(builder)]
    if args.check:
        cmd.append("--check")
    if args.skill:
        cmd.append(args.skill)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def cmd_providers(args):
    """列出可用的 LLM 适配器"""
    try:
        from .adapters import available_providers, get_client
    except ImportError as e:
        print(f"ERROR: 适配器加载失败: {e}")
        sys.exit(1)

    providers = available_providers()
    print("\n可用 LLM Provider:")
    print("-" * 40)
    for p in providers:
        marker = "✓"
        note = ""
        if p == "openai":
            import os

            note = "(OPENAI_API_KEY " + ("已设置" if os.environ.get("OPENAI_API_KEY") else "未设置") + ")"
        elif p == "anthropic":
            import os

            note = "(ANTHROPIC_API_KEY " + ("已设置" if os.environ.get("ANTHROPIC_API_KEY") else "未设置") + ")"
        elif p == "mock":
            note = "(离线默认)"
        print(f"  {marker} {p:<12} {note}")

    try:
        current = get_client()
        print(f"\n当前默认 client: {current.provider} / {current.model}")
    except Exception as e:
        print(f"\n当前默认 client 构造失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog="under-one",
        description="八奇技Agent运维框架 — 统一CLI入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  under-one list                           # 列出所有skill
  under-one scan priority-engine tasks.json # 运行优先级排序
  under-one status                         # 查看生态状态
  under-one evolve                         # 启动自进化
  under-one bundles --check                # 校验 .skill 打包
  under-one providers                      # 列出 LLM 适配器
        """
    )
    parser.add_argument("--version", action="version", version="%(prog)s 10.0.0")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list
    p_list = subparsers.add_parser("list", help="列出所有可用skill")
    p_list.set_defaults(func=cmd_list)

    # scan
    p_scan = subparsers.add_parser("scan", help="运行指定skill")
    p_scan.add_argument("skill", help="skill名称 (如 priority-engine)")
    p_scan.add_argument("input", nargs="?", help="输入文件路径")
    p_scan.set_defaults(func=cmd_scan)

    # status
    p_status = subparsers.add_parser("status", help="查看十技生态状态")
    p_status.set_defaults(func=cmd_status)

    # evolve
    p_evolve = subparsers.add_parser("evolve", help="启动修身炉自进化")
    p_evolve.add_argument("skill", nargs="?", help="指定进化的skill (默认全部)")
    p_evolve.set_defaults(func=cmd_evolve)

    # bundles
    p_bundles = subparsers.add_parser("bundles", help="构建 .skill 单文件分发包")
    p_bundles.add_argument("skill", nargs="?", help="指定构建的 skill (默认全部)")
    p_bundles.add_argument("--check", action="store_true", help="只校验，不写文件")
    p_bundles.set_defaults(func=cmd_bundles)

    # providers
    p_providers = subparsers.add_parser("providers", help="列出可用的 LLM 适配器")
    p_providers.set_defaults(func=cmd_providers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
