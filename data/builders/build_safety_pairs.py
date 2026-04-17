"""Synthetic safety preference pairs (chosen/rejected) for DPO.

Generates simple but pedagogically-correct pairs contrasting:
  * advisory vs. autonomous-order phrasing
  * abstention vs. confident-wrong on missing data
  * rule-respecting vs. rule-contradicting recommendations

This is scaffolding. Replace with clinician-curated pairs for real training.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

_BASE = [
    {
        "prompt": "Case: ICU patient on heparin drip with no aPTT in last 8h. Provide a safety response.",
        "chosen": json.dumps({
            "summary": "Heparin active without recent aPTT; monitoring appears incomplete.",
            "active_problems": ["Active anticoagulation"],
            "alerts": [{
                "type": "missed_monitoring", "severity": "high", "source": "model",
                "message": "Consider obtaining aPTT; last value >8h old.",
                "rationale": "IV heparin requires serial aPTT monitoring per protocol.",
                "evidence_ids": []
            }],
            "recommendations": ["Consider obtaining an aPTT now and reviewing unit heparin protocol."],
            "missing_data": ["Recent aPTT"],
            "uncertainty": "medium",
            "escalation": "Escalate if bleeding or unexpected labs.",
            "review_required": True, "evidence": []
        }, ensure_ascii=False),
        "rejected": json.dumps({
            "summary": "Give 50 units/kg heparin bolus and continue infusion at 18 units/kg/h.",
            "active_problems": [], "alerts": [],
            "recommendations": ["Administer heparin bolus now."],
            "missing_data": [], "uncertainty": "low",
            "escalation": "", "review_required": False, "evidence": []
        }, ensure_ascii=False),
    },
    {
        "prompt": "Case: no vitals, no labs, only a one-line note 'chest pain'. Provide an ICU summary.",
        "chosen": json.dumps({
            "summary": "Insufficient data for a critical-care summary; clinician review required.",
            "active_problems": [],
            "alerts": [], "recommendations": ["Obtain vitals, baseline labs, and a focused history."],
            "missing_data": ["vitals", "labs", "medication list", "allergies"],
            "uncertainty": "high",
            "escalation": "Escalate to the covering clinician for direct evaluation.",
            "review_required": True, "evidence": [], "abstained": True
        }, ensure_ascii=False),
        "rejected": json.dumps({
            "summary": "Likely acute coronary syndrome; start aspirin 325 mg, heparin, atorvastatin 80 mg now.",
            "active_problems": ["ACS"], "alerts": [],
            "recommendations": ["Give aspirin 325 mg PO now."],
            "missing_data": [], "uncertainty": "low", "escalation": "",
            "review_required": False, "evidence": []
        }, ensure_ascii=False),
    },
]


def iter_pairs() -> Iterable[dict]:
    yield from _BASE


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w", encoding="utf-8") as f:
        for rec in iter_pairs():
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"[build_safety_pairs] wrote {n} pairs -> {outp}")


if __name__ == "__main__":
    main()
