"""Strict input validation applied before any business logic.

Provides:
  * ``sanitize_case`` — deep-cleans a raw case dict (length caps, type
    coercion, HTML/injection stripping).
  * ``validate_infer_request`` — raises ``InputValidationError`` with a
    structured list of problems when the payload is unsafe.
  * ``MAX_CASE_PAYLOAD_BYTES`` — hard size gate enforced by the API layer.
"""
from __future__ import annotations

import html
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CASE_PAYLOAD_BYTES: int = 256 * 1024  # 256 KiB — generous for a single case
MAX_STRING_LENGTH: int = 10_000
MAX_LIST_LENGTH: int = 200
MAX_NESTING_DEPTH: int = 8

_STRIP_HTML_RE = re.compile(r"<[^>]+>")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class InputValidationError(Exception):
    """Raised when the incoming payload fails strict validation."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(f"Input validation failed: {problems}")


# ---------------------------------------------------------------------------
# Sanitisation helpers
# ---------------------------------------------------------------------------

def _clean_string(value: str) -> str:
    """Strip HTML tags, control chars, and cap length."""
    value = _STRIP_HTML_RE.sub("", value)
    value = _CONTROL_CHAR_RE.sub("", value)
    value = html.unescape(value)
    return value[:MAX_STRING_LENGTH]


def _sanitize_value(value: Any, *, depth: int = 0) -> Any:
    """Recursively sanitize a JSON-like value."""
    if depth > MAX_NESTING_DEPTH:
        return None

    if isinstance(value, str):
        return _clean_string(value)
    if isinstance(value, dict):
        return {
            _clean_string(str(k)): _sanitize_value(v, depth=depth + 1)
            for k, v in list(value.items())[:MAX_LIST_LENGTH]
        }
    if isinstance(value, list):
        return [
            _sanitize_value(v, depth=depth + 1)
            for v in value[:MAX_LIST_LENGTH]
        ]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    # Unknown type — coerce to string
    return _clean_string(str(value))[:MAX_STRING_LENGTH]


def sanitize_case(case: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-cleaned copy of *case*."""
    return _sanitize_value(case, depth=0)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Strict Pydantic request model (upgrade of the permissive one)
# ---------------------------------------------------------------------------

_ALLOWED_TASKS = frozenset({
    "icu_summary",
    "differential_support",
    "management_assistance",
    "medication_safety",
    "handoff_generation",
})


class StrictInferRequest(BaseModel):
    """Validates shape + tightens constraints beyond what JSON-Schema checks."""
    task: str = "icu_summary"
    case: dict[str, Any] = Field(...)
    use_rag: bool = True
    use_model: bool = True

    @field_validator("task")
    @classmethod
    def _task_must_be_known(cls, v: str) -> str:
        if v not in _ALLOWED_TASKS:
            raise ValueError(f"task must be one of {sorted(_ALLOWED_TASKS)}")
        return v

    @field_validator("case")
    @classmethod
    def _case_must_have_id(cls, v: dict) -> dict:
        if not isinstance(v.get("case_id"), str) or not v["case_id"].strip():
            raise ValueError("case.case_id is required and must be a non-empty string")
        if not isinstance(v.get("demographics"), dict):
            raise ValueError("case.demographics must be a dict")
        return v


def validate_infer_request(raw: dict[str, Any]) -> StrictInferRequest:
    """Parse + validate; raises ``InputValidationError`` on failure."""
    try:
        return StrictInferRequest(**raw)
    except Exception as exc:
        raise InputValidationError([str(exc)]) from exc
