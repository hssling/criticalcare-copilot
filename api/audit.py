"""Audit event schemas.

Each event captures *what happened*, *who*, *when*, and *outcome* in a
structured, JSON-serializable format suitable for compliance logging.

Events are emitted to whatever sink ``emit_audit_event`` is configured with
(defaults to the structured logger). In production, replace the emitter with
your organisation's SIEM / audit backend.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .redaction import redact_dict

log = logging.getLogger("audit")


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

class AuditAction(str, Enum):
    INFER = "infer"
    SAFETY_CHECK = "safety_check"
    RETRIEVE = "retrieve"
    ABSTAIN = "abstain"
    GUARDRAIL_REJECT = "guardrail_reject"
    VALIDATION_FAIL = "validation_fail"
    RATE_LIMIT = "rate_limit"
    CONFIG_CHANGE = "config_change"
    HEALTH_CHECK = "health_check"


class AuditOutcome(str, Enum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILURE = "failure"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Event model
# ---------------------------------------------------------------------------

class AuditEvent(BaseModel):
    """Immutable audit record."""
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: AuditAction
    outcome: AuditOutcome
    request_id: str = "-"
    case_id: str | None = None
    task: str | None = None
    model_version: str | None = None
    rules_fired: list[str] = Field(default_factory=list)
    schema_valid: bool = True
    review_required: bool = True
    latency_ms: float | None = None
    detail: dict[str, Any] = Field(default_factory=dict)

    def redacted_dict(self) -> dict[str, Any]:
        """Serialise with PHI scrubbed."""
        raw = self.model_dump()
        raw["detail"] = redact_dict(raw.get("detail", {}))
        return raw


# ---------------------------------------------------------------------------
# Emitter — swap in production
# ---------------------------------------------------------------------------

_AUDIT_LOG_PATH: str | None = os.getenv("AUDIT_LOG_PATH")


def emit_audit_event(event: AuditEvent) -> None:
    """Write an audit event to the configured sink.

    Default: structured logger + optional append-only file.
    Replace this function body with your SIEM integration in production.
    """
    payload = event.redacted_dict()
    log.info("audit_event", extra={"data": payload})

    path = _AUDIT_LOG_PATH
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
