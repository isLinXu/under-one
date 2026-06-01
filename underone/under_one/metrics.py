"""Formal metrics API for UnderOne.

The standalone skill runtime still carries ``skills/metrics_collector.py`` so
bundled skills can run without installing the SDK. This module is the stable
package-level import surface used by SDK and CLI code.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _load_metrics_module() -> Any:
    try:
        from skills import metrics_collector

        return metrics_collector
    except ImportError:
        helper = Path(__file__).resolve().parent.parent / "skills" / "metrics_collector.py"
        if not helper.exists():
            raise
        spec = importlib.util.spec_from_file_location("under_one_metrics_collector", helper)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load metrics helper: {helper}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


_metrics = _load_metrics_module()

resolve_runtime_data_dir = _metrics.resolve_runtime_data_dir
resolve_runtime_metrics_file = _metrics.resolve_runtime_metrics_file
record_metrics = _metrics.record_metrics
record_metric_manual = _metrics.record_metric_manual
get_recent_metrics = _metrics.get_recent_metrics
get_all_skills_metrics = _metrics.get_all_skills_metrics
format_prometheus_metrics = _metrics.format_prometheus_metrics
resource_snapshot = _metrics.resource_snapshot
create_prometheus_server = _metrics.create_prometheus_server

__all__ = [
    "resolve_runtime_data_dir",
    "resolve_runtime_metrics_file",
    "record_metrics",
    "record_metric_manual",
    "get_recent_metrics",
    "get_all_skills_metrics",
    "format_prometheus_metrics",
    "resource_snapshot",
    "create_prometheus_server",
]
