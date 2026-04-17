"""Canonical severity levels and banned-phrase lexicon for guardrails."""
from __future__ import annotations

SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def severity_rank(s: str) -> int:
    try:
        return SEVERITY_ORDER.index(s)
    except ValueError:
        return -1


# Patterns that indicate the model is issuing autonomous orders rather than
# review-required suggestions. These are regex-safe literal fragments.
AUTONOMOUS_ORDER_PATTERNS = [
    r"\bgive\s+\d+\s*(mg|g|mcg|units?)\b",
    r"\badminister\s+\d+\s*(mg|g|mcg|units?)\b",
    r"\bstart\s+(norepinephrine|epinephrine|heparin|insulin)\b[^.]*\bnow\b",
    r"\border\s+\d+\s*(mg|g|mcg|units?)\b",
    r"\bbolus\s+\d+\s*(ml|cc|l)\b",
]

# Phrases that are safe/advisory wording we prefer.
ADVISORY_STEMS = [
    "consider",
    "review",
    "discuss with",
    "escalate",
    "reassess",
    "re-evaluate",
    "if clinically appropriate",
]


HIGH_RISK_DRUG_CLASSES = {
    "vasopressor",
    "anticoagulant",
    "insulin",
    "sedative",
    "opioid",
    "neuromuscular_blocker",
    "antiarrhythmic",
    "paralytic",
}
