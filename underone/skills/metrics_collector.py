#!/usr/bin/env python3
"""
Skill Metrics Collector — 运行时指标统一收集模块
供各 Skill 脚本通过装饰器自动记录执行指标。

Usage:
    from metrics_collector import record_metrics

    @record_metrics("qiti-yuanliu")
    def scan(context):
        ...

记录字段：
    skill_name, timestamp, duration_ms, success, quality_score,
    error_count, human_intervention, output_completeness, consistency_score
"""

import json
import time
import functools
from pathlib import Path
from datetime import datetime
from typing import Callable, Any, Optional

# 运行时数据目录
DEFAULT_DATA_DIR = Path("runtime_data")


def _ensure_dir(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)


def _write_metric(skill_name: str, metric: dict, data_dir: Path) -> None:
    _ensure_dir(data_dir)
    file_path = data_dir / f"{skill_name}_metrics.jsonl"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(metric, ensure_ascii=False) + "\n")


def _coerce_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _nested_value(payload: Any, *path: str) -> Any:
    current = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _infer_quality_score(result: Any) -> float:
    if not isinstance(result, dict):
        return 85.0

    candidate_paths = [
        (("quality_score",), lambda x: x),
        (("health_score",), lambda x: x),
        (("avg_quality",), lambda x: x),
        (("avg_digestion_rate",), lambda x: x),
        (("ecosystem_quality",), lambda x: x),
        (("score",), lambda x: x),
        (("metrics", "health_score"), lambda x: x),
        (("identity_integrity",), lambda x: x * 100.0),
        (("deviation_score",), lambda x: 100.0 - x * 100.0),
        (("contamination_risk", "score"), lambda x: 100.0 - x * 100.0),
        (("hallucination_risk", "score"), lambda x: 100.0 - x * 100.0),
        (("monte_carlo", "on_time_rate"), lambda x: x),
    ]
    for path, transform in candidate_paths:
        raw = _nested_value(result, *path)
        numeric = _coerce_number(raw)
        if numeric is not None:
            return round(_clamp_score(transform(numeric)), 1)

    return 85.0


def _infer_output_completeness(result: Any) -> float:
    if not isinstance(result, dict):
        return 100.0

    candidate_paths = [
        (("output_completeness",), lambda x: x),
        (("completeness",), lambda x: x),
        (("coverage",), lambda x: x),
        (("metrics", "completeness"), lambda x: x),
    ]
    for path, transform in candidate_paths:
        raw = _nested_value(result, *path)
        numeric = _coerce_number(raw)
        if numeric is not None:
            return round(_clamp_score(transform(numeric)), 1)

    if result.get("files"):
        return 100.0
    return 100.0


def _infer_consistency_score(result: Any, fallback_quality: float) -> float:
    if not isinstance(result, dict):
        return fallback_quality

    candidate_paths = [
        (("consistency_score",), lambda x: x),
        (("consistency",), lambda x: x),
        (("metrics", "consistency"), lambda x: x),
        (("identity_integrity",), lambda x: x * 100.0),
    ]
    for path, transform in candidate_paths:
        raw = _nested_value(result, *path)
        numeric = _coerce_number(raw)
        if numeric is not None:
            return round(_clamp_score(transform(numeric)), 1)

    return round(_clamp_score(fallback_quality), 1)


def _infer_human_intervention(result: Any) -> float:
    if not isinstance(result, dict):
        return 0.0

    for path in (("human_intervention",), ("escalation_contract", "manual_review_required")):
        raw = _nested_value(result, *path)
        numeric = _coerce_number(raw)
        if numeric is not None:
            return round(max(0.0, numeric), 2)

    surgery_mode = result.get("surgery_mode")
    if surgery_mode in {"review", "seal"}:
        return 1.0

    return 0.0


def _infer_error_count(result: Any, default_error_count: int) -> int:
    if not isinstance(result, dict):
        return default_error_count

    numeric = _coerce_number(result.get("error_count"))
    if numeric is not None:
        return max(0, int(round(numeric)))

    errors = result.get("errors")
    if isinstance(errors, list):
        return len(errors)

    return default_error_count


def record_metrics(
    skill_name: str,
    data_dir: Optional[Path] = None,
    quality_fn: Optional[Callable[[Any], float]] = None,
    completeness_fn: Optional[Callable[[Any], float]] = None,
):
    """
    装饰器：自动记录 Skill 执行指标。

    Args:
        skill_name: Skill 标识名，如 "qiti-yuanliu"
        data_dir: metrics 输出目录，默认 runtime_data/
        quality_fn: 可选。从返回值提取 quality_score 的函数。
        completeness_fn: 可选。从返回值提取 output_completeness 的函数。

    Example:
        @record_metrics("qiti-yuanliu")
        def scan(context):
            return {"health_score": 85, ...}
    """
    _data_dir = data_dir or DEFAULT_DATA_DIR

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            success = True
            error_count = 0
            result = None

            try:
                result = func(*args, **kwargs)
            except Exception:
                success = False
                error_count = 1
                raise
            finally:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)

                # 自动提取 quality_score
                quality_score = 85.0
                if quality_fn and result is not None:
                    try:
                        quality_score = _clamp_score(float(quality_fn(result)))
                    except Exception:
                        pass
                else:
                    quality_score = _infer_quality_score(result)

                # 自动提取 output_completeness
                output_completeness = 100.0
                if completeness_fn and result is not None:
                    try:
                        output_completeness = _clamp_score(float(completeness_fn(result)))
                    except Exception:
                        pass
                else:
                    output_completeness = _infer_output_completeness(result)

                # 启发式：consistency_score
                consistency_score = _infer_consistency_score(result, quality_score)
                human_intervention = _infer_human_intervention(result)
                error_count = _infer_error_count(result, error_count)

                metric = {
                    "skill_name": skill_name,
                    "timestamp": datetime.now().isoformat(),
                    "duration_ms": duration_ms,
                    "success": success,
                    "quality_score": round(quality_score, 1),
                    "error_count": error_count,
                    "human_intervention": human_intervention,
                    "output_completeness": round(output_completeness, 1),
                    "consistency_score": round(consistency_score, 1),
                }
                _write_metric(skill_name, metric, _data_dir)

            return result

        return wrapper
    return decorator


def record_metric_manual(
    skill_name: str,
    duration_ms: float,
    success: bool = True,
    quality_score: float = 85.0,
    error_count: int = 0,
    human_intervention: int = 0,
    output_completeness: float = 100.0,
    consistency_score: float = 85.0,
    data_dir: Optional[Path] = None,
) -> None:
    """
    手动记录一条指标（适用于无法使用装饰器的场景）。

    Example:
        record_metric_manual(
            skill_name="juling-qianjiang",
            duration_ms=150.5,
            success=True,
            quality_score=92.0,
        )
    """
    _data_dir = data_dir or DEFAULT_DATA_DIR
    metric = {
        "skill_name": skill_name,
        "timestamp": datetime.now().isoformat(),
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "quality_score": round(quality_score, 1),
        "error_count": error_count,
        "human_intervention": human_intervention,
        "output_completeness": round(output_completeness, 1),
        "consistency_score": round(consistency_score, 1),
    }
    _write_metric(skill_name, metric, _data_dir)


def get_recent_metrics(skill_name: str, n: int = 30, data_dir: Optional[Path] = None) -> list:
    """
    读取最近 N 条指标记录。

    Example:
        records = get_recent_metrics("qiti-yuanliu", n=10)
        avg_quality = sum(r["quality_score"] for r in records) / len(records)
    """
    _data_dir = data_dir or DEFAULT_DATA_DIR
    file_path = _data_dir / f"{skill_name}_metrics.jsonl"
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    records = [json.loads(line) for line in lines]
    return records[-n:]


def get_all_skills_metrics(data_dir: Optional[Path] = None) -> dict:
    """
    读取所有 Skill 的最近指标。

    Returns:
        {skill_name: [metrics...]}
    """
    _data_dir = data_dir or DEFAULT_DATA_DIR
    result = {}
    for file_path in _data_dir.glob("*_metrics.jsonl"):
        skill_name = file_path.name.replace("_metrics.jsonl", "")
        result[skill_name] = get_recent_metrics(skill_name, n=100, data_dir=_data_dir)
    return result


if __name__ == "__main__":
    # 简单自测
    @record_metrics("test-skill")
    def demo_task(fail: bool = False):
        if fail:
            raise ValueError("demo error")
        return {"health_score": 95.0}

    print("=== Metrics Collector Self-Test ===")
    demo_task()
    try:
        demo_task(fail=True)
    except ValueError:
        pass

    records = get_recent_metrics("test-skill", n=10)
    print(f"Recorded {len(records)} metrics for test-skill")
    for r in records:
        print(f"  success={r['success']} quality={r['quality_score']} duration={r['duration_ms']}ms")
