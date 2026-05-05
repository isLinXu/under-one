#!/usr/bin/env python3
"""
under-one.skills V10 八卦阵生态中枢 (Bagua-Zhen V10 Coordinator)
用途: 八奇技skill生态系统的中央协调器
- 扫描所有skill状态
- 互斥检测与仲裁
- 效能聚合评分
- V10: 生态健康报告 + 联动调度 + 十技全景

Usage:
    python coordinator.py [skills_dir]
"""

import json, sys
from pathlib import Path
from datetime import datetime

# V10.1: 支持从 under-one.yaml 读取互斥/协同矩阵
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from _skill_config import get_skill_config
except ImportError:
    def get_skill_config(_section, _key=None, default=None):
        return default

SKILL_NAMES = [
    "qiti-yuanliu", "tongtian-lu", "dalu-dongguan", "shenji-bailian",
    "fenghou-qimen", "liuku-xianzei", "shuangquanshou", "juling-qianjiang",
    "bagua-zhen", "xiushen-lu",
]

# 从配置读取互斥/协同矩阵，回退到硬编码默认值
_cfg_mutex = get_skill_config("baguazhen", "mutex_pairs", [])
_cfg_synergy = get_skill_config("baguazhen", "synergy_pairs", [])

MUTEX_PAIRS = [
    tuple(p) for p in _cfg_mutex
] if _cfg_mutex else [
    ("tongtian-lu", "shenji-bailian"),
    ("qiti-yuanliu", "fenghou-qimen"),
    ("dalu-dongguan", "liuku-xianzei"),
]

SYNERGY_PAIRS = [
    tuple(p) for p in _cfg_synergy
] if _cfg_synergy else [
    ("tongtian-lu", "dalu-dongguan"),
    ("juling-qianjiang", "shenji-bailian"),
    ("qiti-yuanliu", "shuangquanshou"),
]


def load_metrics(skill_name: str) -> list:
    file_path = Path("runtime_data") / f"{skill_name}_metrics.jsonl"
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()][-30:]


def calc_stats(records):
    if not records:
        return {"success_rate": 0, "quality": 85, "errors": 0, "n": 0}
    n = len(records)
    return {
        "success_rate": round(sum(1 for r in records if r.get("success")) / n * 100, 1),
        "quality": round(sum(r.get("quality_score", 0) for r in records) / n, 1),
        "errors": round(sum(r.get("error_count", 0) for r in records) / n, 2),
        "n": n,
    }


def _default_skills_dir() -> str:
    """默认 skills 目录（相对此脚本向上两级 = underone/skills/）"""
    from pathlib import Path as _P
    return str(_P(__file__).resolve().parent.parent.parent)


def coordinate(skills_dir: str = None):
    """V10生态协调"""
    if skills_dir is None:
        skills_dir = _default_skills_dir()
    print(f"\n{'='*60}")
    print("☯ under-one.skills V10 八卦阵 · 十技生态全景")
    print(f"{'='*60}")

    # 收集所有skill状态
    states = {}
    active_count = 0
    for sid in SKILL_NAMES:
        records = load_metrics(sid)
        stats = calc_stats(records)
        states[sid] = stats
        if stats["n"] > 0:
            active_count += 1

    # 互斥检测
    mutex_found = []
    for a, b in MUTEX_PAIRS:
        if states[a]["n"] > 0 and states[b]["n"] > 0:
            mutex_found.append((a, b))

    # 协同检测
    synergy_found = []
    for a, b in SYNERGY_PAIRS:
        if states[a]["n"] > 0 and states[b]["n"] > 0:
            synergy_found.append((a, b))

    # 效能聚合
    scores = [s["quality"] for s in states.values() if s["n"] > 0]
    avg = sum(scores) / len(scores) if scores else 85
    level = "阵法大成" if avg >= 90 else "阵法稳固" if avg >= 75 else "阵法松动"

    # 打印全景
    print(f"\n生态状态: {level} | 平均分: {avg:.1f} | 活跃: {active_count}/10")
    if mutex_found:
        print(f"互斥检测: {len(mutex_found)} 对skill同时活跃")
        for a, b in mutex_found:
            print(f"  ⚠ {a} ↔ {b}")
    if synergy_found:
        print(f"协同增益: {len(synergy_found)} 对skill协同生效")
        for a, b in synergy_found:
            print(f"  ✓ {a} + {b}")

    print(f"\n{'Skill':<20} {'成功率':>6} {'质量':>6} {'错误':>6} {'样本':>4} {'状态':>6}")
    print("-" * 60)
    for sid in SKILL_NAMES:
        s = states[sid]
        status = "活跃" if s["n"] > 0 else "休眠"
        print(f"{sid:<20} {s['success_rate']:>5.0f}% {s['quality']:>5.1f} {s['errors']:>5.2f} {s['n']:>4d} {status:>6}")

    # 生成报告
    report = {
        "coordinator": "bagua-zhen",
        "version": "10.0",
        "ecosystem_level": level,
        "average_quality": round(avg, 1),
        "active_skills": active_count,
        "mutex_pairs": mutex_found,
        "synergy_pairs": synergy_found,
        "skill_states": states,
        "timestamp": datetime.now().isoformat(),
    }

    out = Path("ecosystem_report_v10.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告: {out}")
    return report


def main():
    skills_dir = sys.argv[1] if len(sys.argv) > 1 else _default_skills_dir()
    coordinate(skills_dir)


if __name__ == "__main__":
    main()
