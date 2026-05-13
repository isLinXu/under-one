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
from itertools import combinations

# 运行时指标收集
SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SKILLS_ROOT))
try:
    from metrics_collector import record_metrics
except ImportError:
    def record_metrics(*args, **kwargs):
        def decorator(f): return f
        return decorator

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
VERSION = "v0.1.0"

# 从配置读取互斥/协同矩阵，回退到硬编码默认值
_cfg_mutex = get_skill_config("baguazhen", "mutex_pairs", [])
_cfg_synergy = get_skill_config("baguazhen", "synergy_pairs", [])
_cfg_min_cooccurrence = get_skill_config("baguazhen", "min_cooccurrence_for_dynamic", 3)
_cfg_cache_ttl = get_skill_config("baguazhen", "cache_ttl_seconds", 3600)
_cfg_prefer_dynamic = get_skill_config("baguazhen", "prefer_dynamic_overrides", True)
_cfg_dynamic_ignore_pairs = get_skill_config("baguazhen", "dynamic_ignore_pairs", [])

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

# V10.2: 动态关系缓存文件
DYNAMIC_REL_FILE = Path("runtime_data") / "_dynamic_relationships.json"


def _pair_key(pair) -> tuple[str, str]:
    return tuple(sorted(pair))


IGNORED_DYNAMIC_PAIRS = {_pair_key(pair) for pair in _cfg_dynamic_ignore_pairs}


def _filter_dynamic_relationships(relationships: dict) -> dict:
    filtered = {}
    for key, rel in relationships.items():
        pair = rel.get("pair", [])
        if len(pair) != 2:
            continue
        if _pair_key(pair) in IGNORED_DYNAMIC_PAIRS:
            continue
        filtered[key] = rel
    return filtered


def _merge_relationships(dynamic_rels: dict) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    mutex_map = {_pair_key(pair): tuple(pair) for pair in MUTEX_PAIRS}
    synergy_map = {_pair_key(pair): tuple(pair) for pair in SYNERGY_PAIRS}

    for rel in dynamic_rels.values():
        pair = rel.get("pair", [])
        if len(pair) != 2:
            continue
        pair_key = _pair_key(pair)
        rel_pair = tuple(pair)
        rel_type = rel.get("type")

        if rel_type == "mutex":
            mutex_map[pair_key] = rel_pair
            if _cfg_prefer_dynamic:
                synergy_map.pop(pair_key, None)
        elif rel_type == "synergy":
            synergy_map[pair_key] = rel_pair
            if _cfg_prefer_dynamic:
                mutex_map.pop(pair_key, None)

    return list(mutex_map.values()), list(synergy_map.values())


def _ecosystem_quality(report: dict) -> float:
    """Derive a coordination-quality score from ecosystem-wide stability."""
    if not isinstance(report, dict):
        return 85.0
    base = float(report.get("average_quality", 85.0))
    active_skills = float(report.get("active_skills", 0))
    mutex_count = len(report.get("mutex_pairs", []))
    synergy_count = len(report.get("synergy_pairs", []))
    level = report.get("ecosystem_level")
    avg_human = float(report.get("average_human_intervention", 0.0) or 0.0)

    bonus = min(12.0, active_skills * 0.5 + synergy_count * 0.4)
    if level == "阵法大成":
        bonus += 3.0
    elif level == "阵法稳固":
        bonus += 7.0
    penalty = mutex_count * 0.8 + avg_human * 6.0
    return round(min(100.0, max(base, base + bonus - penalty)), 1)


def _load_dynamic_relationships(min_cooccurrence: int = 3) -> dict:
    """V10.2: 从runtime_data动态学习互斥/协同关系。

    算法:
    1. 加载所有skill的metrics记录
    2. 按时间窗口(小时)统计共现
    3. 比较共现时的质量/错误率 vs 单独运行时的质量/错误率
    4. 若共现时错误率显著升高 -> 标记互斥
    5. 若共现时质量显著升高 -> 标记协同
    """
    # 优先使用缓存（如果1小时内已更新）
    if DYNAMIC_REL_FILE.exists():
        try:
            with open(DYNAMIC_REL_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            cached_time = datetime.fromisoformat(cached.get("updated_at", "2000-01-01"))
            if (datetime.now() - cached_time).total_seconds() < _cfg_cache_ttl:
                return _filter_dynamic_relationships(cached.get("relationships", {}))
        except Exception:
            pass

    # 加载所有记录
    all_records = {}
    for sid in SKILL_NAMES:
        all_records[sid] = load_metrics(sid)

    # 计算共现统计
    rel_stats = {}
    for a, b in combinations(SKILL_NAMES, 2):
        if _pair_key((a, b)) in IGNORED_DYNAMIC_PAIRS:
            continue
        rec_a = all_records.get(a, [])
        rec_b = all_records.get(b, [])
        if not rec_a or not rec_b:
            continue

        # 提取时间戳（按小时分组）
        hours_a = set()
        hours_b = set()
        for r in rec_a:
            ts = r.get("timestamp", "")
            if ts:
                hours_a.add(ts[:13])  # 精确到小时: YYYY-MM-DDTHH
        for r in rec_b:
            ts = r.get("timestamp", "")
            if ts:
                hours_b.add(ts[:13])

        cooccurrence_hours = hours_a & hours_b
        total_co = len(cooccurrence_hours)

        if total_co < min_cooccurrence:
            continue

        # 计算单独运行与共现时的指标
        solo_a = [r for r in rec_a if r.get("timestamp", "")[:13] not in hours_b]
        solo_b = [r for r in rec_b if r.get("timestamp", "")[:13] not in hours_a]
        co_a = [r for r in rec_a if r.get("timestamp", "")[:13] in cooccurrence_hours]
        co_b = [r for r in rec_b if r.get("timestamp", "")[:13] in cooccurrence_hours]

        def _avg_quality(recs):
            vals = [r.get("quality_score", 0) for r in recs if r.get("quality_score") is not None]
            return sum(vals) / len(vals) if vals else 0

        def _avg_errors(recs):
            vals = [r.get("error_count", 0) for r in recs]
            return sum(vals) / len(vals) if vals else 0

        if not (solo_a or solo_b):
            continue

        solo_q = (_avg_quality(solo_a) + _avg_quality(solo_b)) / 2
        co_q = (_avg_quality(co_a) + _avg_quality(co_b)) / 2 if co_a or co_b else 0
        solo_e = (_avg_errors(solo_a) + _avg_errors(solo_b)) / 2
        co_e = (_avg_errors(co_a) + _avg_errors(co_b)) / 2 if co_a or co_b else 0

        rel_stats[f"{a}__{b}"] = {
            "cooccurrence": total_co,
            "solo_quality": round(solo_q, 1),
            "co_quality": round(co_q, 1),
            "solo_errors": round(solo_e, 2),
            "co_errors": round(co_e, 2),
        }

    # 判断关系
    relationships = {}
    for key, stats in rel_stats.items():
        a, b = key.split("__", 1)
        rel_type = None
        reason = None

        quality_delta = stats["co_quality"] - stats["solo_quality"]
        error_delta = stats["co_errors"] - stats["solo_errors"]
        mutex_score = 0.0
        synergy_score = 0.0

        if stats["solo_errors"] > 0:
            mutex_score = max(mutex_score, stats["co_errors"] / max(stats["solo_errors"], 0.01))
        if stats["solo_quality"] > 0:
            quality_ratio = stats["co_quality"] / max(stats["solo_quality"], 1)
            if quality_ratio < 0.8:
                mutex_score = max(mutex_score, 1 / max(quality_ratio, 0.01))
            if quality_ratio > 1.2 and stats["co_errors"] <= stats["solo_errors"] * 1.1 + 0.05:
                synergy_score = max(synergy_score, quality_ratio)

        if error_delta > 0.15:
            mutex_score = max(mutex_score, 1.5 + error_delta)

        if mutex_score >= 1.5 and mutex_score >= synergy_score:
            rel_type = "mutex"
            if error_delta > 0.15:
                reason = f"共现时错误率{stats['co_errors']:.2f} > 单独{stats['solo_errors']:.2f}"
            else:
                reason = f"共现时质量{stats['co_quality']:.1f} < 单独{stats['solo_quality']:.1f}"
        elif synergy_score >= 1.2:
            rel_type = "synergy"
            reason = f"共现时质量{stats['co_quality']:.1f} > 单独{stats['solo_quality']:.1f}"

        if rel_type:
            relationships[key] = {
                "pair": [a, b],
                "type": rel_type,
                "reason": reason,
                "stats": stats,
            }

    # 缓存结果
    try:
        DYNAMIC_REL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DYNAMIC_REL_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "updated_at": datetime.now().isoformat(),
                "relationships": relationships,
                "source": "dynamic_analysis",
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return _filter_dynamic_relationships(relationships)


def load_metrics(skill_name: str) -> list:
    file_path = Path("runtime_data") / f"{skill_name}_metrics.jsonl"
    if not file_path.exists():
        return []
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            records.append(record)
    return records[-30:]


def calc_stats(records):
    if not records:
        return {"success_rate": 0, "quality": 85, "errors": 0, "human_intervention": 0, "output_completeness": 0, "consistency_score": 85, "n": 0}
    n = len(records)
    return {
        "success_rate": round(sum(1 for r in records if r.get("success")) / n * 100, 1),
        "quality": round(sum(r.get("quality_score", 0) for r in records) / n, 1),
        "errors": round(sum(r.get("error_count", 0) for r in records) / n, 2),
        "human_intervention": round(sum(r.get("human_intervention", 0) for r in records) / n, 2),
        "output_completeness": round(sum(r.get("output_completeness", 0) for r in records) / n, 1),
        "consistency_score": round(sum(r.get("consistency_score", r.get("quality_score", 0)) for r in records) / n, 1),
        "n": n,
    }


def _default_skills_dir() -> str:
    """默认 skills 目录（相对此脚本向上两级 = underone/skills/）"""
    from pathlib import Path as _P
    return str(_P(__file__).resolve().parent.parent.parent)


@record_metrics("bagua-zhen", quality_fn=_ecosystem_quality)
def coordinate(skills_dir: str = None):
    """V10生态协调"""
    if skills_dir is None:
        skills_dir = _default_skills_dir()
    print(f"\n{'='*60}")
    print(f"☯ under-one.skills V{VERSION} 八卦阵 · 十技生态全景")
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

    # V10.2: 加载动态关系并合并到默认矩阵
    dynamic_rels = _load_dynamic_relationships(min_cooccurrence=_cfg_min_cooccurrence)
    all_mutex, all_synergy = _merge_relationships(dynamic_rels)

    # 互斥检测
    mutex_found = []
    for a, b in all_mutex:
        if states[a]["n"] > 0 and states[b]["n"] > 0:
            reason = ""
            for r in dynamic_rels.values():
                if r["pair"] == [a, b] or r["pair"] == [b, a]:
                    reason = f" ({r['reason']})"
                    break
            mutex_found.append((a, b, reason))

    # 协同检测
    synergy_found = []
    for a, b in all_synergy:
        if states[a]["n"] > 0 and states[b]["n"] > 0:
            reason = ""
            for r in dynamic_rels.values():
                if r["pair"] == [a, b] or r["pair"] == [b, a]:
                    reason = f" ({r['reason']})"
                    break
            synergy_found.append((a, b, reason))

    # 效能聚合
    scores = [s["quality"] for s in states.values() if s["n"] > 0]
    human_signals = [s["human_intervention"] for s in states.values() if s["n"] > 0]
    avg = sum(scores) / len(scores) if scores else 85
    avg_human = sum(human_signals) / len(human_signals) if human_signals else 0
    level = "阵法大成" if avg >= 90 else "阵法稳固" if avg >= 75 else "阵法松动"

    # 打印全景
    print(f"\n生态状态: {level} | 平均分: {avg:.1f} | 人工介入: {avg_human:.2f} | 活跃: {active_count}/10")
    if mutex_found:
        print(f"互斥检测: {len(mutex_found)} 对skill同时活跃")
        for a, b, reason in mutex_found:
            print(f"  ⚠ {a} ↔ {b}{reason}")
    if synergy_found:
        print(f"协同增益: {len(synergy_found)} 对skill协同生效")
        for a, b, reason in synergy_found:
            print(f"  ✓ {a} + {b}{reason}")

    print(f"\n{'Skill':<20} {'成功率':>6} {'质量':>6} {'错误':>6} {'样本':>4} {'状态':>6}")
    print("-" * 60)
    for sid in SKILL_NAMES:
        s = states[sid]
        status = "活跃" if s["n"] > 0 else "休眠"
        print(f"{sid:<20} {s['success_rate']:>5.0f}% {s['quality']:>5.1f} {s['errors']:>5.2f} {s['n']:>4d} {status:>6}")

    # 生成报告
    report = {
        "coordinator": "bagua-zhen",
        "version": VERSION,
        "ecosystem_level": level,
        "average_quality": round(avg, 1),
        "ecosystem_quality": _ecosystem_quality({
            "average_quality": round(avg, 1),
            "average_human_intervention": round(avg_human, 2),
            "active_skills": active_count,
            "mutex_pairs": [[a, b] for a, b, _ in mutex_found],
            "synergy_pairs": [[a, b] for a, b, _ in synergy_found],
            "ecosystem_level": level,
        }),
        "output_completeness": 100.0 if active_count else 0.0,
        "average_human_intervention": round(avg_human, 2),
        "active_skills": active_count,
        "mutex_pairs": [[a, b] for a, b, _ in mutex_found],
        "synergy_pairs": [[a, b] for a, b, _ in synergy_found],
        "dynamic_relationships": dynamic_rels,
        "relationship_policy": {
            "prefer_dynamic_overrides": _cfg_prefer_dynamic,
            "dynamic_ignore_pairs": sorted([list(pair) for pair in IGNORED_DYNAMIC_PAIRS]),
        },
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
