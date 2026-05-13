#!/usr/bin/env python3
"""
under-one.skills 统一CLI入口

Usage:
    under-one --help
    under-one list                             # 列出所有可用skill
    under-one scan <skill> <input>             # 运行指定skill
    under-one audit [skill]                    # 审计skill结构与元数据
    under-one status                           # 查看十技生态状态
    under-one evolve [skill]                   # 启动修身炉进化
    under-one bundles [--check] [skill]        # 构建 .skill 单文件分发包
    under-one install-host --host qclaw        # 安装到指定宿主
    under-one install-host --host custom --dest /tmp/custom-skills   # 第三方产品
    under-one hosts                            # 列出支持的宿主及别名
    under-one providers                        # 列出可用 LLM 适配器
"""

import argparse
import json
import sys
from pathlib import Path

from .skill_bundle import install_bundle, verify_installed_skill
from .skill_audit import audit_skill_dir, audit_skills_root, write_audit_report
from .hosted_skills import (
    DEFAULT_SKILLS,
    accepted_host_names,
    available_hosts,
    default_host_skills_root,
    get_host_profile,
    host_aliases_for,
    install_and_validate_host_skill,
    iter_source_skill_dirs,
    resolve_host_target_root,
)
from .skill_lifecycle import SKILL_TEST_TARGETS, validate_skill

SKILL_MAP = {
    "context-guard":      ("qiti-yuanliu",       "scripts/entropy_scanner.py",   "本源自省"),
    "command-factory":    ("tongtian-lu",        "scripts/fu_generator.py",      "符阵编排"),
    "insight-radar":      ("dalu-dongguan",      "scripts/link_detector.py",     "异常洞观"),
    "tool-forge":         ("shenji-bailian",     "scripts/tool_factory.py",      "炼器造物"),
    "priority-engine":    ("fenghou-qimen",      "scripts/priority_engine.py",   "全局排盘"),
    "knowledge-digest":   ("liuku-xianzei",      "scripts/knowledge_digest.py",  "掠夺消化"),
    "persona-guard":      ("shuangquanshou",     "scripts/dna_validator.py",     "记忆人格手术"),
    "tool-orchestrator":  ("juling-qianjiang",   "scripts/dispatcher.py",        "灵体统御"),
    "ecosystem-hub":      ("bagua-zhen",         "scripts/coordinator.py",       "阵法中枢"),
    "evolution-engine":   ("xiushen-lu",         "scripts/core_engine.py",       "跨技进化"),
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
    cmd = [sys.executable, str(script_path)]
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
        subprocess.run([sys.executable, str(coord_script)])
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


def cmd_audit(args):
    """审计 skill 结构、元数据和入口约定"""
    skill_dir = find_skill_dir()
    if args.skill:
        if args.skill not in SKILL_MAP:
            print(f"ERROR: 未知skill '{args.skill}'。运行 'under-one list' 查看可用skill。")
            sys.exit(1)
        result = audit_skill_dir(skill_dir / SKILL_MAP[args.skill][0]).to_dict()
        payload = {
            "ok": result["ok"],
            "skill_count": 1,
            "ok_count": 1 if result["ok"] else 0,
            "warning_count": len(result["warnings"]),
            "error_count": len(result["errors"]),
            "results": [result],
        }
    else:
        payload = audit_skills_root(skill_dir)

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        write_audit_report(payload, out_path)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("\nSkill 审计结果")
        print("-" * 40)
        for item in payload["results"]:
            status = "OK" if item["ok"] else "FAIL"
            print(f"[{status}] {item['skill']}")
            for err in item["errors"]:
                print(f"  error: {err}")
            for warn in item["warnings"]:
                print(f"  warn: {warn}")
        print("-" * 40)
        print(
            f"skills={payload['skill_count']} ok={payload['ok_count']} "
            f"warnings={payload['warning_count']} errors={payload['error_count']}"
        )
        if args.output:
            print(f"report={out_path}")
    sys.exit(0 if payload["error_count"] == 0 else 1)


def cmd_evolve(args):
    """启动修身炉进化"""
    skill_dir = find_skill_dir()
    engine_script = skill_dir / "xiushen-lu/scripts/core_engine.py"
    
    if not engine_script.exists():
        print("ERROR: 修身炉引擎不存在")
        sys.exit(1)
    
    import subprocess
    cmd = [sys.executable, str(engine_script), str(skill_dir)]
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

    cmd = [sys.executable, str(builder)]
    if args.check:
        cmd.append("--check")
    if args.skill:
        cmd.append(args.skill)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def cmd_install_bundle(args):
    """安装单个 .skill 分发包"""
    bundle_path = Path(args.bundle).expanduser().resolve()
    if not bundle_path.exists():
        print(f"ERROR: 找不到 bundle: {bundle_path}")
        sys.exit(1)

    target_root = Path(args.target_dir).expanduser().resolve()
    result = install_bundle(bundle_path, target_root, force=args.force)
    print(
        f"✓ installed {result['name']} -> {result['target_dir']} "
        f"({result['file_count']} files)"
    )


def cmd_hosts(args):
    """列出支持的宿主安装运行时。"""
    print("\n支持的宿主 Runtime:")
    print("-" * 50)
    for host in available_hosts():
        profile = get_host_profile(host)
        try:
            root = str(default_host_skills_root(host))
        except ValueError:
            root = "<requires --dest>"
        mode = "frontmatter-wrapper" if profile.layout == "frontmatter" else "native-source"
        extras = "agents/openai.yaml" if profile.uses_agents_yaml else "-"
        print(f"  {profile.name:<10} {profile.label:<12} layout={mode:<20} root={root}")
        print(f"             extra_files={extras}")
        aliases = host_aliases_for(host)
        if aliases:
            print(f"             aliases={', '.join(aliases)}")


def cmd_install_host(args):
    """安装 skills 到指定宿主目录。"""
    selected = args.skills or DEFAULT_SKILLS
    unknown = [name for name in selected if name not in DEFAULT_SKILLS]
    if unknown:
        print(f"ERROR: 未知 skill: {unknown}")
        sys.exit(2)

    profile = get_host_profile(args.host)
    try:
        dest = resolve_host_target_root(args.host, args.dest)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(2)
    source_root = find_skill_dir()

    results = []
    for skill_dir in iter_source_skill_dirs(source_root, selected):
        result = install_and_validate_host_skill(
            skill_dir,
            args.host,
            target_root=dest,
            force=args.force,
            include_source_validation=not args.skip_source_validation,
        )
        results.append(result)

    payload = {
        "host": profile.name,
        "target_root": str(dest),
        "skills_total": len(results),
        "skills_passed": sum(1 for item in results if item["overall_passed"]),
        "results": results,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{profile.label} target: {dest}")
        print("")
        for idx, item in enumerate(results, start=1):
            install = item["install"]
            host_validation = install["host_validation"]
            lifecycle = install["installed_lifecycle"]
            print(f"[{idx}/{len(results)}] {item['skill']}")
            print(f"  installed_dir: {item['installed_dir']}")
            print(f"  {profile.name}_discovery: {'PASS' if host_validation['passed'] else 'FAIL'}")
            print(f"  installed_self_test: {'PASS' if lifecycle['passed'] else 'FAIL'}")
            print(f"  overall: {'PASS' if item['overall_passed'] else 'FAIL'}")
            if host_validation["errors"]:
                print(f"  {profile.name}_errors: {host_validation['errors']}")
            if host_validation["warnings"]:
                print(f"  {profile.name}_warnings: {host_validation['warnings']}")
            print("")
        print(f"summary: {payload['skills_passed']}/{payload['skills_total']} passed")
    sys.exit(0 if payload["skills_passed"] == payload["skills_total"] else 1)


def cmd_test_skill(args):
    """针对单个 skill 运行独立测试"""
    skill_path_arg = getattr(args, "path", None)
    if skill_path_arg:
        skill_path = Path(skill_path_arg).expanduser().resolve()
        test_script = skill_path / "tests" / "self_test.py"
        if not test_script.exists():
            print(f"ERROR: 未找到已安装 skill 的 self_test.py: {test_script}")
            sys.exit(1)
        import subprocess

        result = subprocess.run([sys.executable, str(test_script)], cwd=str(skill_path))
        sys.exit(result.returncode)

    if not args.skill or args.skill not in SKILL_MAP:
        print(f"ERROR: 未知skill '{args.skill}'。运行 'under-one list' 查看可用skill。")
        sys.exit(1)

    skill_name, _, _ = SKILL_MAP[args.skill]
    targets = SKILL_TEST_TARGETS.get(skill_name, {})
    if args.suite == "all":
        selectors = targets.get("core", []) + targets.get("sdk", [])
    else:
        selectors = targets.get(args.suite, [])
    if not selectors:
        print(f"ERROR: 未找到 {skill_name} 的测试选择器")
        sys.exit(1)

    tests_root = Path(__file__).resolve().parent.parent / "tests"
    if not tests_root.exists():
        print("WARNING: 当前安装不包含 tests/，退回到验证场景。")
        skill_dir = find_skill_dir() / skill_name
        report = validate_skill(skill_name, skill_dir)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report["validation_passed"] else 1)

    import subprocess

    cmd = [sys.executable, "-m", "pytest", *selectors, "-q"]
    result = subprocess.run(cmd, cwd=str(Path(__file__).resolve().parent.parent.parent))
    sys.exit(result.returncode)


def cmd_validate_skill(args):
    """针对单个 skill 运行独立验证"""
    skill_path_arg = getattr(args, "path", None)
    if skill_path_arg:
        skill_dir = Path(skill_path_arg).expanduser().resolve()
        audit = audit_skill_dir(skill_dir).to_dict()
        if (skill_dir / "skillctl.py").exists():
            installed_check = verify_installed_skill(skill_dir)
            validation_passed = audit["ok"] and installed_check["passed"]
            effect_summary = "installed skill structural validation + standalone lifecycle check"
            recommendations = [] if validation_passed else [
                "Inspect audit errors and installed skill lifecycle results before using this standalone skill."
            ]
        else:
            installed_check = {
                "passed": True,
                "skill": skill_dir.name,
                "mode": "structural_only",
                "validate": {"returncode": 0, "stdout": "", "stderr": ""},
                "self_test": {"returncode": 0, "stdout": "", "stderr": ""},
            }
            validation_passed = audit["ok"]
            effect_summary = "installed skill structural validation only"
            recommendations = [] if validation_passed else [
                "Inspect audit errors before using this standalone skill."
            ]
        report = {
            "skill": skill_dir.name,
            "validation_passed": validation_passed,
            "audit": audit,
            "scenario": {"effect_summary": effect_summary},
            "independent_lifecycle": installed_check,
            "recommendations": recommendations,
        }
    else:
        if not args.skill or args.skill not in SKILL_MAP:
            print(f"ERROR: 未知skill '{args.skill}'。运行 'under-one list' 查看可用skill。")
            sys.exit(1)

        skill_name, _, _ = SKILL_MAP[args.skill]
        skill_dir = find_skill_dir() / skill_name
        report = validate_skill(skill_name, skill_dir)

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"report={out_path}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if report["validation_passed"] else "FAIL"
        print(f"{skill_name}: {status}")
        print(report["scenario"]["effect_summary"])
    sys.exit(0 if report["validation_passed"] else 1)


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
  under-one audit                          # 审计skill结构与元数据
  under-one status                         # 查看生态状态
  under-one evolve                         # 启动自进化
  under-one bundles --check                # 校验 .skill 打包
  under-one install-bundle foo.skill       # 安装单个 skill bundle
  under-one hosts                          # 列出支持的宿主
  under-one install-host --host workbuddy  # 安装到 WorkBuddy
  under-one install-host --host custom --dest /tmp/custom-skills fenghou-qimen
  under-one test-skill priority-engine       # 单 skill 测试
  under-one test-skill --path ~/.under-one/skills/fenghou-qimen
  under-one validate-skill priority-engine   # 单 skill 验证
  under-one validate-skill --path ~/.under-one/skills/fenghou-qimen
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

    # audit
    p_audit = subparsers.add_parser("audit", help="审计skill结构与元数据")
    p_audit.add_argument("skill", nargs="?", help="指定审计的skill (默认全部)")
    p_audit.add_argument("--json", action="store_true", help="输出JSON结果")
    p_audit.add_argument("--output", help="将审计结果写入JSON文件")
    p_audit.set_defaults(func=cmd_audit)

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

    # install-bundle
    p_install = subparsers.add_parser("install-bundle", help="安装单个 .skill 分发包")
    p_install.add_argument("bundle", help=".skill bundle 文件路径")
    p_install.add_argument("--target-dir", default=str(Path.home() / ".under-one" / "skills"), help="安装目标目录")
    p_install.add_argument("--force", action="store_true", help="覆盖已存在的同名 skill")
    p_install.set_defaults(func=cmd_install_bundle)

    # hosts
    p_hosts = subparsers.add_parser("hosts", help="列出支持的宿主 Runtime")
    p_hosts.set_defaults(func=cmd_hosts)

    # install-host
    p_install_host = subparsers.add_parser("install-host", help="安装 skills 到指定宿主（含 custom 第三方产品）")
    p_install_host.add_argument("skills", nargs="*", help="skill names to install; defaults to all")
    p_install_host.add_argument("--host", choices=accepted_host_names(), default="codex", help="目标宿主 Runtime")
    p_install_host.add_argument("--dest", help="覆盖默认宿主技能目录")
    p_install_host.add_argument("--force", action="store_true", help="覆盖已存在的同名 skill")
    p_install_host.add_argument("--skip-source-validation", action="store_true", help="跳过源码侧验证")
    p_install_host.add_argument("--json", action="store_true", help="输出 JSON 报告")
    p_install_host.set_defaults(func=cmd_install_host)

    # test-skill
    p_test = subparsers.add_parser("test-skill", help="针对单个 skill 运行独立测试")
    p_test.add_argument("skill", nargs="?", help="skill 名称 (如 priority-engine)")
    p_test.add_argument("--path", help="已安装 skill 目录路径（用于独立测试）")
    p_test.add_argument("--suite", choices=["core", "sdk", "all"], default="all", help="测试套件")
    p_test.set_defaults(func=cmd_test_skill)

    # validate-skill
    p_validate = subparsers.add_parser("validate-skill", help="针对单个 skill 运行独立验证")
    p_validate.add_argument("skill", nargs="?", help="skill 名称 (如 priority-engine)")
    p_validate.add_argument("--path", help="已安装 skill 目录路径（用于独立验证）")
    p_validate.add_argument("--json", action="store_true", help="输出JSON结果")
    p_validate.add_argument("--output", help="将验证结果写入JSON文件")
    p_validate.set_defaults(func=cmd_validate_skill)

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
