"""Output guardrails applied to model responses before returning to the UI.

Responsibilities:
  * enforce ``review_required = True``
  * scan for autonomous-order phrasing and rewrite/redact
  * ensure required fields exist (even if empty)
  * bump escalation text when critical alerts are present
"""
from __future__ import annotations

import re
from typing import Any

from .risk_labels import AUTONOMOUS_ORDER_PATTERNS, severity_rank


class GuardrailError(Exception):
    """Raised when output cannot be safely salvaged."""


_ORDER_RE = re.compile("|".join(AUTONOMOUS_ORDER_PATTERNS), re.IGNORECASE)


def _advisory_rewrite(text: str) -> str:
    """Rewrite an imperative phrase into an advisory one."""
    if not text:
        return text
    return _ORDER_RE.sub(lambda m: f"consider reviewing ({m.group(0)})", text)


def enforce_guardrails(resp: dict[str, Any]) -> dict[str, Any]:
    """Mutate & return ``resp`` in place with guardrails applied.

    Raises ``GuardrailError`` if the response is structurally unusable.
    """
    if not isinstance(resp, dict):
        raise GuardrailError("response is not an object")

    # Structural defaults
    resp.setdefault("summary", "")
    resp.setdefault("active_problems", [])
    resp.setdefault("alerts", [])
    resp.setdefault("recommendations", [])
    resp.setdefault("missing_data", [])
    resp.setdefault("uncertainty", "high")
    resp.setdefault("escalation", "")
    resp.setdefault("evidence", [])
    resp["review_required"] = True  # invariant

    # Rewrite imperative/autonomous phrasing in free-text fields
    resp["summary"] = _advisory_rewrite(resp.get("summary", ""))
    resp["recommendations"] = [_advisory_rewrite(r) for r in resp.get("recommendations", [])]
    for a in resp.get("alerts", []):
        if "message" in a:
            a["message"] = _advisory_rewrite(a["message"])
        if "rationale" in a and a["rationale"]:
            a["rationale"] = _advisory_rewrite(a["rationale"])

    # Critical alerts -> ensure escalation string is non-empty
    top = max((severity_rank(a.get("severity", "low")) for a in resp["alerts"]), default=-1)
    if top >= severity_rank("high") and not resp["escalation"].strip():
        resp["escalation"] = (
            "Critical-severity alert(s) present. Escalate to the covering intensivist "
            "and re-verify key data points before acting."
        )

    # Uncertainty sanity
    if resp["uncertainty"] not in ("low", "medium", "high"):
        resp["uncertainty"] = "high"

    return resp
