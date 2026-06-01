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

import functools
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Optional

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on some platforms.
    resource = None

RUNTIME_DIR_ENV = "UNDER_ONE_RUNTIME_DIR"
DEFAULT_DATA_DIR = Path("runtime_data")


def resolve_runtime_data_dir(data_dir: Optional[Any] = None) -> Path:
    """Resolve the metrics directory, honoring explicit overrides and env sandboxes."""
    if data_dir is not None:
        return Path(data_dir).expanduser()
    override = os.getenv(RUNTIME_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return DEFAULT_DATA_DIR


def resolve_runtime_metrics_file(skill_name: str, data_dir: Optional[Any] = None) -> Path:
    return resolve_runtime_data_dir(data_dir) / f"{skill_name}_metrics.jsonl"


def _ensure_dir(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)


def _write_metric(skill_name: str, metric: dict, data_dir: Path) -> None:
    _ensure_dir(data_dir)
    file_path = data_dir / f"{skill_name}_metrics.jsonl"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(metric, ensure_ascii=False) + "\n")


def _get_runtime_config(key: Optional[str] = None, default: Any = None) -> Any:
    try:
        from under_one.config import get_config

        return get_config("runtime", key, default)
    except Exception:
        try:
            from _skill_config import get_config

            return get_config("runtime", key, default)
        except Exception:
            return default


def resource_snapshot() -> dict:
    """Return a best-effort process resource snapshot using only stdlib APIs."""

    if resource is None:
        return {
            "available": False,
            "peak_memory_mb": None,
            "cpu_time_ms": None,
        }

    usage = resource.getrusage(resource.RUSAGE_SELF)
    raw_rss = float(getattr(usage, "ru_maxrss", 0.0) or 0.0)
    if sys.platform == "darwin":
        peak_memory_mb = raw_rss / (1024 * 1024)
    else:
        peak_memory_mb = raw_rss / 1024
    cpu_time_ms = (float(usage.ru_utime) + float(usage.ru_stime)) * 1000
    return {
        "available": True,
        "peak_memory_mb": round(max(0.0, peak_memory_mb), 2),
        "cpu_time_ms": round(max(0.0, cpu_time_ms), 2),
    }


def _resource_limits() -> dict:
    limits = _get_runtime_config("resource_limits", {}) or {}
    if not isinstance(limits, dict):
        return {}
    return limits


def _limit_value(limits: dict, key: str) -> Optional[float]:
    value = _coerce_number(limits.get(key))
    if value is None or value <= 0:
        return None
    return value


def _resource_warnings(metric: dict) -> list:
    limits = _resource_limits()
    warnings = []
    checks = [
        ("duration_ms", "warn_duration_ms", "duration_warn"),
        ("duration_ms", "max_duration_ms", "duration_limit"),
        ("peak_memory_mb", "warn_peak_memory_mb", "memory_warn"),
        ("peak_memory_mb", "max_peak_memory_mb", "memory_limit"),
    ]
    for metric_key, limit_key, warning_type in checks:
        limit = _limit_value(limits, limit_key)
        current = _coerce_number(metric.get(metric_key))
        if limit is None or current is None:
            continue
        if current > limit:
            warnings.append(
                {
                    "type": warning_type,
                    "metric": metric_key,
                    "value": round(current, 3),
                    "limit": round(limit, 3),
                }
            )
    return warnings


def _iter_jsonl_records(file_path: Path) -> list:
    if not file_path.exists():
        return []
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


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


def _infer_quality_score(result: Any) -> Optional[float]:
    if not isinstance(result, dict):
        return None

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

    return None


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

    structural_signals = [
        "execution_contract",
        "dispatch_contract",
        "safety_contract",
        "approval_contract",
        "execution_policy",
        "repair_plan",
        "stability_contract",
        "priority_actions",
        "command_packets",
        "review_schedule",
        "portfolio_diagnostics",
        "evolution_backlog",
        "pattern_summary",
        "skill_contract",
        "execution_summary",
    ]
    structural_count = sum(1 for key in structural_signals if result.get(key))
    if result.get("files"):
        return 100.0
    if structural_count >= 4:
        return 100.0
    if structural_count >= 2:
        return 95.0
    if structural_count == 1:
        return 90.0
    return 100.0


def _infer_consistency_score(result: Any, fallback_quality: Optional[float]) -> Optional[float]:
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

    if result.get("approval_contract", {}).get("approval_status") == "blocked":
        return round(_clamp_score(max(fallback_quality or 0.0, 92.0)), 1)
    if result.get("execution_policy", {}).get("mode") == "plan-only":
        return round(_clamp_score(max(fallback_quality or 0.0, 90.0)), 1)
    if result.get("execution_contract", {}).get("resume_ready") is True:
        return round(_clamp_score(max(fallback_quality or 0.0, 88.0)), 1)
    if result.get("priority_actions") and not result.get("alerts"):
        return round(_clamp_score(max(fallback_quality or 0.0, 86.0)), 1)
    if fallback_quality is None:
        return None
    return round(_clamp_score(fallback_quality), 1)


def _infer_human_intervention(result: Any) -> float:
    if not isinstance(result, dict):
        return 0.0

    raw_direct = _nested_value(result, "human_intervention")
    direct_numeric = _coerce_number(raw_direct)
    if direct_numeric is not None:
        return round(max(0.0, direct_numeric), 2)

    approval_contract = result.get("approval_contract")
    if isinstance(approval_contract, dict):
        approval_status = approval_contract.get("approval_status")
        if approval_status == "blocked":
            return 0.0
        if approval_contract.get("manual_review_required"):
            return 1.0

    execution_policy = result.get("execution_policy")
    if isinstance(execution_policy, dict) and execution_policy.get("mode") == "plan-only":
        if execution_policy.get("manual_gate_required"):
            return 1.0
        return 0.0

    for path in (("escalation_contract", "manual_review_required"),):
        raw = _nested_value(result, *path)
        numeric = _coerce_number(raw)
        if numeric is not None:
            return round(max(0.0, numeric), 2)

    surgery_mode = result.get("surgery_mode")
    if surgery_mode == "review":
        return 1.0
    if surgery_mode == "seal":
        return 0.0

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
                resources = resource_snapshot()

                # 自动提取 quality_score；无法评估时保留 None，不再伪装成高质量。
                quality_score = None
                if quality_fn and result is not None:
                    try:
                        quality_score = _clamp_score(float(quality_fn(result)))
                    except Exception:
                        quality_score = None
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
                    "quality_score": round(quality_score, 1) if quality_score is not None else None,
                    "quality_assessed": quality_score is not None,
                    "error_count": error_count,
                    "human_intervention": human_intervention,
                    "output_completeness": round(output_completeness, 1),
                    "consistency_score": round(consistency_score, 1) if consistency_score is not None else None,
                    "peak_memory_mb": resources.get("peak_memory_mb"),
                    "cpu_time_ms": resources.get("cpu_time_ms"),
                }
                warnings = _resource_warnings(metric)
                metric["resource_warnings"] = warnings
                metric["resource_budget_exceeded"] = any(item.get("type", "").endswith("_limit") for item in warnings)
                _write_metric(skill_name, metric, resolve_runtime_data_dir(data_dir))

            return result

        return wrapper
    return decorator


def record_metric_manual(
    skill_name: str,
    duration_ms: float,
    success: bool = True,
    quality_score: Optional[float] = None,
    error_count: int = 0,
    human_intervention: int = 0,
    output_completeness: float = 100.0,
    consistency_score: Optional[float] = None,
    peak_memory_mb: Optional[float] = None,
    cpu_time_ms: Optional[float] = None,
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
    _data_dir = resolve_runtime_data_dir(data_dir)
    metric = {
        "skill_name": skill_name,
        "timestamp": datetime.now().isoformat(),
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "quality_score": round(quality_score, 1) if quality_score is not None else None,
        "quality_assessed": quality_score is not None,
        "error_count": error_count,
        "human_intervention": human_intervention,
        "output_completeness": round(output_completeness, 1),
        "consistency_score": round(consistency_score, 1) if consistency_score is not None else None,
        "peak_memory_mb": round(peak_memory_mb, 2) if peak_memory_mb is not None else None,
        "cpu_time_ms": round(cpu_time_ms, 2) if cpu_time_ms is not None else None,
    }
    warnings = _resource_warnings(metric)
    metric["resource_warnings"] = warnings
    metric["resource_budget_exceeded"] = any(item.get("type", "").endswith("_limit") for item in warnings)
    _write_metric(skill_name, metric, _data_dir)


def get_recent_metrics(skill_name: str, n: int = 30, data_dir: Optional[Path] = None) -> list:
    """
    读取最近 N 条指标记录。

    Example:
        records = get_recent_metrics("qiti-yuanliu", n=10)
        avg_quality = sum(r["quality_score"] for r in records) / len(records)
    """
    _data_dir = resolve_runtime_data_dir(data_dir)
    file_path = resolve_runtime_metrics_file(skill_name, _data_dir)
    records = _iter_jsonl_records(file_path)
    return records[-n:]


def get_all_skills_metrics(data_dir: Optional[Path] = None) -> dict:
    """
    读取所有 Skill 的最近指标。

    Returns:
        {skill_name: [metrics...]}
    """
    _data_dir = resolve_runtime_data_dir(data_dir)
    result = {}
    for file_path in _data_dir.glob("*_metrics.jsonl"):
        skill_name = file_path.name.replace("_metrics.jsonl", "")
        result[skill_name] = get_recent_metrics(skill_name, n=100, data_dir=_data_dir)
    return result


def _prom_label(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _average_numeric(records: list, field: str) -> Optional[float]:
    values = [
        float(item[field])
        for item in records
        if isinstance(item, dict) and isinstance(item.get(field), (int, float))
    ]
    if not values:
        return None
    return sum(values) / len(values)


def format_prometheus_metrics(data_dir: Optional[Path] = None) -> str:
    """Render recent JSONL metrics in Prometheus text exposition format."""

    all_metrics = get_all_skills_metrics(data_dir)
    lines = [
        "# HELP under_one_skill_runs_total Total recorded skill runs by result.",
        "# TYPE under_one_skill_runs_total counter",
    ]
    for skill_name, records in sorted(all_metrics.items()):
        success_count = sum(1 for item in records if item.get("success") is True)
        failure_count = sum(1 for item in records if item.get("success") is False)
        label = _prom_label(skill_name)
        lines.append(f'under_one_skill_runs_total{{skill_name="{label}",success="true"}} {success_count}')
        lines.append(f'under_one_skill_runs_total{{skill_name="{label}",success="false"}} {failure_count}')

    lines.extend([
        "# HELP under_one_skill_duration_ms_avg Average skill duration in milliseconds.",
        "# TYPE under_one_skill_duration_ms_avg gauge",
    ])
    for skill_name, records in sorted(all_metrics.items()):
        avg_duration = _average_numeric(records, "duration_ms")
        if avg_duration is None:
            continue
        lines.append(f'under_one_skill_duration_ms_avg{{skill_name="{_prom_label(skill_name)}"}} {avg_duration:.3f}')

    for field, metric_name, help_text in [
        ("quality_score", "under_one_skill_quality_score_avg", "Average assessed quality score."),
        ("output_completeness", "under_one_skill_output_completeness_avg", "Average output completeness score."),
        ("consistency_score", "under_one_skill_consistency_score_avg", "Average consistency score."),
        ("human_intervention", "under_one_skill_human_intervention_avg", "Average human intervention signal."),
        ("error_count", "under_one_skill_error_count_avg", "Average error count."),
        ("peak_memory_mb", "under_one_skill_peak_memory_mb_avg", "Average process peak memory observed during skill runs."),
        ("cpu_time_ms", "under_one_skill_cpu_time_ms_avg", "Average process CPU time observed during skill runs."),
    ]:
        lines.extend([f"# HELP {metric_name} {help_text}", f"# TYPE {metric_name} gauge"])
        for skill_name, records in sorted(all_metrics.items()):
            avg = _average_numeric(records, field)
            if avg is None:
                continue
            lines.append(f'{metric_name}{{skill_name="{_prom_label(skill_name)}"}} {avg:.3f}')

    lines.extend([
        "# HELP under_one_skill_resource_budget_exceeded_total Recorded runs that exceeded configured resource limits.",
        "# TYPE under_one_skill_resource_budget_exceeded_total counter",
    ])
    for skill_name, records in sorted(all_metrics.items()):
        count = sum(1 for item in records if item.get("resource_budget_exceeded") is True)
        lines.append(f'under_one_skill_resource_budget_exceeded_total{{skill_name="{_prom_label(skill_name)}"}} {count}')

    return "\n".join(lines) + "\n"


def create_prometheus_server(host: str = "127.0.0.1", port: int = 9465, data_dir: Optional[Path] = None):
    """Create a small stdlib HTTP server exposing /metrics and /-/healthy."""

    resolved_data_dir = resolve_runtime_data_dir(data_dir)

    class MetricsHandler(BaseHTTPRequestHandler):
        server_version = "UnderOneMetrics/1.0"

        def do_GET(self):
            if self.path in {"/-/healthy", "/healthz"}:
                body = b"ok\n"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path != "/metrics":
                body = b"not found\n"
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            body = format_prometheus_metrics(resolved_data_dir).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002 - stdlib signature.
            return

    return ThreadingHTTPServer((host, int(port)), MetricsHandler)


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
