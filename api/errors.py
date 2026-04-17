"""Safe, user-facing error messages.

Internal stack traces and raw exception details MUST NOT reach the frontend.
This module maps internal error types to sanitised HTTP error bodies suitable
for clinician-facing UIs.

Every response includes a stable ``error_code`` that can be looked up in
docs without exposing internals.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error codes → user-safe messages
# ---------------------------------------------------------------------------

_ERROR_MAP: dict[str, dict[str, Any]] = {
    "INPUT_VALIDATION_FAILED": {
        "status": 400,
        "message": "The submitted case data did not pass validation. "
                   "Please check required fields and try again.",
    },
    "PAYLOAD_TOO_LARGE": {
        "status": 413,
        "message": "The submitted case payload exceeds the maximum allowed size.",
    },
    "RATE_LIMIT_EXCEEDED": {
        "status": 429,
        "message": "Too many requests. Please wait a moment and try again.",
    },
    "MODEL_UNAVAILABLE": {
        "status": 503,
        "message": "The clinical decision-support model is temporarily unavailable. "
                   "Rule-based safety checks are still active.",
    },
    "GUARDRAIL_REJECTED": {
        "status": 200,  # still return 200 — body.abstained = true
        "message": "The response was rejected by safety guardrails. "
                   "Clinician review is required.",
    },
    "INTERNAL_ERROR": {
        "status": 500,
        "message": "An unexpected error occurred. A reference ID has been logged "
                   "for investigation. Please try again or escalate to support.",
    },
}


def safe_error_response(
    error_code: str,
    *,
    reference_id: str | None = None,
    extra_detail: str | None = None,
    internal_exc: Exception | None = None,
) -> dict[str, Any]:
    """Return a sanitised error payload safe for the frontend.

    ``reference_id`` lets support correlate a user-visible error with the
    server-side structured log entry.
    """
    ref = reference_id or uuid.uuid4().hex[:12]
    entry = _ERROR_MAP.get(error_code, _ERROR_MAP["INTERNAL_ERROR"])

    # Log the real detail server-side only
    if internal_exc:
        log.error(
            "safe_error reference=%s code=%s",
            ref, error_code,
            exc_info=internal_exc,
            extra={"data": {"error_code": error_code, "reference_id": ref}},
        )

    body: dict[str, Any] = {
        "ok": False,
        "error_code": error_code,
        "message": entry["message"],
        "reference_id": ref,
    }
    if extra_detail:
        body["detail"] = extra_detail
    return {"status": entry["status"], "body": body}
