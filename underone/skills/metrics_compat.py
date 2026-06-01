"""Metrics helpers with a single no-op fallback for standalone skill scripts."""

from pathlib import Path

try:
    from under_one.metrics import record_metrics, resolve_runtime_data_dir
except ImportError:
    try:
        from metrics_collector import record_metrics, resolve_runtime_data_dir
    except ImportError:
        try:
            from .metrics_collector import record_metrics, resolve_runtime_data_dir
        except ImportError:

            def record_metrics(*args, **kwargs):
                def decorator(func):
                    return func

                return decorator

            def resolve_runtime_data_dir(data_dir=None):
                return Path(data_dir or "runtime_data").expanduser()
