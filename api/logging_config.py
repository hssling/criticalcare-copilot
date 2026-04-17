"""Structured JSON logging for production.

Call ``configure_logging()`` once at startup.  All modules then use the
standard ``logging.getLogger(__name__)`` pattern and automatically get
JSON-formatted, context-enriched log records.

Features:
  * JSON lines to stdout (12-factor friendly).
  * ``request_id`` injected via ``set_request_context``.
  * Sensitive fields redacted before emission.
  * Log-level driven by ``LOG_LEVEL`` env var (default ``INFO``).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from .redaction import redact_dict

# ---------------------------------------------------------------------------
# Request-scoped context
# ---------------------------------------------------------------------------

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_request_task: ContextVar[str] = ContextVar("request_task", default="-")


def set_request_context(*, request_id: str, task: str = "-") -> None:
    _request_id.set(request_id)
    _request_task.set(task)


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class _JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line.  Extra ``data`` dict is redacted."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": _request_id.get("-"),
            "task": _request_task.get("-"),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = traceback.format_exception(*record.exc_info)

        # Allow extra structured data via  logger.info("msg", extra={"data": {...}})
        data = getattr(record, "data", None)
        if isinstance(data, dict):
            entry["data"] = redact_dict(data)

        return json.dumps(entry, default=str)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def configure_logging() -> None:
    """Call once at process start."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level, logging.INFO))
    # Suppress noisy third-party loggers
    for name in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)
