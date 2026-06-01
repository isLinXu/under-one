"""Logging helpers for UnderOne."""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Small JSON formatter for log aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:
        entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "skill": getattr(record, "skill_name", "unknown"),
            "message": record.getMessage(),
        }
        for attr in ("event", "trace_id", "span_id", "duration_ms", "status"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        if hasattr(record, "metrics"):
            entry["metrics"] = getattr(record, "metrics")
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def get_logger(name: str = "under-one", *, structured: bool = False) -> logging.Logger:
    """Return a configured UnderOne logger."""

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        if structured:
            handler.setFormatter(StructuredFormatter())
        else:
            handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


@contextmanager
def log_span(logger: logging.Logger, event: str, *, skill_name: str = "unknown", trace_id: str | None = None):
    """Emit start/end JSON log records around a critical path."""

    span_id = uuid.uuid4().hex[:12]
    trace = trace_id or uuid.uuid4().hex
    start = time.perf_counter()
    logger.info(
        f"{event} started",
        extra={"event": event, "skill_name": skill_name, "trace_id": trace, "span_id": span_id, "status": "started"},
    )
    try:
        yield {"trace_id": trace, "span_id": span_id}
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            f"{event} failed",
            extra={
                "event": event,
                "skill_name": skill_name,
                "trace_id": trace,
                "span_id": span_id,
                "duration_ms": duration_ms,
                "status": "failed",
            },
        )
        raise
    else:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            f"{event} completed",
            extra={
                "event": event,
                "skill_name": skill_name,
                "trace_id": trace,
                "span_id": span_id,
                "duration_ms": duration_ms,
                "status": "completed",
            },
        )
