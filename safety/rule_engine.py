"""Deterministic rule engine.

Rules are defined in YAML files under ``rules/``. Each rule has a ``when``
block evaluated against a normalized case dict; if it matches, a ``RuleHit``
is produced. The engine is intentionally simple and explainable — no
arbitrary code execution in YAML.

Supported ``when`` primitives:
  * ``med_name_any_of``:          [str]
  * ``med_class_any_of``:         [str]         (requires ``med.indication`` or class map)
  * ``med_duplicate_class``:      str           (>=2 active meds of class)
  * ``allergy_any_of``:           [str]         (substance on allergy list)
  * ``lab_above``:                {name, value}
  * ``lab_below``:                {name, value}
  * ``lab_missing_for_hours``:    {name, hours}
  * ``diagnosis_any_of``:         [str]
  * ``on_med_any_of``:            [str]
  * ``not_on_med_any_of``:        [str]
  * ``egfr_below``:               number         (computed from creatinine if present)
  * ``age_years_above``:          number

All fields are ANDed within a ``when`` block.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

DEFAULT_RULES_DIR = Path(__file__).resolve().parents[1] / "rules"


@dataclass
class RuleHit:
    rule_id: str
    type: str
    severity: str
    message: str
    rationale: str = ""
    source: str = "rule"

    def to_alert(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
            "rationale": self.rationale,
            "rule_id": self.rule_id,
            "evidence_ids": [],
        }


@dataclass
class _Rule:
    id: str
    type: str
    severity: str
    message: str
    rationale: str
    when: dict[str, Any] = field(default_factory=dict)


def load_rule_packs(rules_dir: str | Path | None = None) -> list[_Rule]:
    rules_dir = Path(rules_dir) if rules_dir else DEFAULT_RULES_DIR
    rules: list[_Rule] = []
    for path in sorted(rules_dir.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        pack_type = doc.get("type", path.stem)
        for r in doc.get("rules", []):
            rules.append(_Rule(
                id=r["id"],
                type=r.get("type", pack_type),
                severity=r.get("severity", "medium"),
                message=r["message"],
                rationale=r.get("rationale", ""),
                when=r.get("when", {}),
            ))
    return rules


# ---------------------------------------------------------------------------
# Matchers
# ---------------------------------------------------------------------------

def _active_meds(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [m for m in case.get("medications", []) if m.get("status", "active") == "active"]


def _lower(xs: Iterable[str]) -> list[str]:
    return [x.lower() for x in xs]


def _estimate_egfr(case: dict[str, Any]) -> float | None:
    """Very rough Cockcroft-Gault-style estimate; used only for rule gating."""
    demo = case.get("demographics", {})
    age = demo.get("age_years")
    sex = demo.get("sex")
    weight = demo.get("weight_kg")
    if age is None or weight is None:
        return None
    # Latest creatinine
    creats = [lab for lab in case.get("labs", [])
              if str(lab.get("name", "")).lower() in {"creatinine", "scr", "serum_creatinine"}]
    if not creats:
        return None
    try:
        latest = sorted(creats, key=lambda l: l.get("ts", ""))[-1]
        scr = float(latest["value"])
    except (ValueError, KeyError, TypeError):
        return None
    if scr <= 0:
        return None
    crcl = ((140 - age) * weight) / (72 * scr)
    if sex == "F":
        crcl *= 0.85
    return crcl


def _match(rule: _Rule, case: dict[str, Any]) -> bool:
    w = rule.when
    if not w:
        return False

    meds = _active_meds(case)
    med_names = _lower(m.get("name", "") for m in meds)
    med_classes = _lower(m.get("class", "") for m in meds if m.get("class"))
    allergies = _lower(a.get("substance", "") for a in case.get("allergies", []))
    diagnoses = _lower(d.get("label", "") for d in case.get("diagnoses", []))

    if "med_name_any_of" in w:
        if not any(n.lower() in med_names for n in w["med_name_any_of"]):
            return False
    if "med_class_any_of" in w:
        if not any(c.lower() in med_classes for c in w["med_class_any_of"]):
            return False
    if "med_duplicate_class" in w:
        cls = w["med_duplicate_class"].lower()
        if med_classes.count(cls) < 2:
            return False
    if "allergy_any_of" in w:
        if not any(s.lower() in allergies for s in w["allergy_any_of"]):
            return False
    if "on_med_any_of" in w:
        if not any(n.lower() in med_names for n in w["on_med_any_of"]):
            return False
    if "not_on_med_any_of" in w:
        if any(n.lower() in med_names for n in w["not_on_med_any_of"]):
            return False
    if "diagnosis_any_of" in w:
        if not any(d.lower() in " ".join(diagnoses) for d in w["diagnosis_any_of"]):
            return False
    if "lab_above" in w:
        name = w["lab_above"]["name"].lower()
        thr = float(w["lab_above"]["value"])
        vals = [float(l["value"]) for l in case.get("labs", [])
                if str(l.get("name", "")).lower() == name and _is_num(l.get("value"))]
        if not vals or max(vals) <= thr:
            return False
    if "lab_below" in w:
        name = w["lab_below"]["name"].lower()
        thr = float(w["lab_below"]["value"])
        vals = [float(l["value"]) for l in case.get("labs", [])
                if str(l.get("name", "")).lower() == name and _is_num(l.get("value"))]
        if not vals or min(vals) >= thr:
            return False
    if "lab_missing_for_hours" in w:
        name = w["lab_missing_for_hours"]["name"].lower()
        hours = float(w["lab_missing_for_hours"]["hours"])
        latest_ts = _latest_ts(case.get("labs", []), name)
        if latest_ts is None:
            return True
        admit = _parse_ts(case.get("icu_stay", {}).get("icu_admit_ts"))
        ref = _utcnow() if admit is None else admit
        if (ref - latest_ts).total_seconds() / 3600.0 < hours:
            return False
    if "egfr_below" in w:
        egfr = _estimate_egfr(case)
        if egfr is None or egfr >= float(w["egfr_below"]):
            return False
    if "age_years_above" in w:
        age = case.get("demographics", {}).get("age_years")
        if age is None or age <= float(w["age_years_above"]):
            return False
    return True


def _is_num(v: Any) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _latest_ts(items: list[dict[str, Any]], name: str) -> datetime | None:
    best: datetime | None = None
    for it in items:
        if str(it.get("name", "")).lower() != name:
            continue
        ts = _parse_ts(it.get("ts"))
        if ts and (best is None or ts > best):
            best = ts
    return best


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    def __init__(self, rules_dir: str | Path | None = None):
        self._rules = load_rule_packs(rules_dir)

    @property
    def rules(self) -> list[_Rule]:
        return self._rules

    def evaluate(self, case: dict[str, Any]) -> list[RuleHit]:
        hits: list[RuleHit] = []
        for r in self._rules:
            try:
                if _match(r, case):
                    hits.append(RuleHit(
                        rule_id=r.id, type=r.type, severity=r.severity,
                        message=r.message, rationale=r.rationale,
                    ))
            except Exception as exc:  # never let a single rule break the engine
                hits.append(RuleHit(
                    rule_id=r.id, type="other", severity="low",
                    message=f"Rule {r.id} failed to evaluate",
                    rationale=f"internal: {exc!s}",
                ))
        return hits
