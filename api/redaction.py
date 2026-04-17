"""Redaction hooks for sensitive / PHI fields.

``redact_dict`` recursively walks a dict and replaces values whose keys
match known-sensitive patterns with ``"[REDACTED]"``.  Additional keys can
be registered at runtime via ``register_sensitive_key``.

Used by:
  * ``logging_config._JSONFormatter``  — prevents PHI in log lines.
  * ``audit.AuditEvent``               — strips PHI before persistence.
  * ``CopilotService``                 — optional pre-return scrub.
"""
from __future__ import annotations

import copy
import re
from typing import Any

# ---------------------------------------------------------------------------
# Default sensitive-key patterns (case-insensitive substring match)
# ---------------------------------------------------------------------------

_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"patient.?name",
        r"mrn",
        r"medical.?record",
        r"ssn",
        r"social.?security",
        r"dob",
        r"date.?of.?birth",
        r"address",
        r"phone",
        r"email",
        r"insurance",
        r"token",
        r"password",
        r"secret",
        r"api.?key",
        r"authorization",
    ]
]

REDACTED = "[REDACTED]"


def register_sensitive_key(pattern: str) -> None:
    """Add a regex pattern to the global redaction list."""
    _SENSITIVE_PATTERNS.append(re.compile(pattern, re.IGNORECASE))


def _is_sensitive(key: str) -> bool:
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def redact_dict(data: dict[str, Any], *, _depth: int = 0) -> dict[str, Any]:
    """Return a deep copy with sensitive leaf values replaced."""
    if _depth > 12:
        return {}
    out: dict[str, Any] = {}
    for k, v in data.items():
        if _is_sensitive(str(k)):
            out[k] = REDACTED
        elif isinstance(v, dict):
            out[k] = redact_dict(v, _depth=_depth + 1)
        elif isinstance(v, list):
            out[k] = [
                redact_dict(i, _depth=_depth + 1) if isinstance(i, dict) else i
                for i in v
            ]
        else:
            out[k] = v
    return out


def redact_case_for_logging(case: dict[str, Any]) -> dict[str, Any]:
    """Convenience: deep-copy + redact a clinical case before logging."""
    return redact_dict(copy.deepcopy(case))
