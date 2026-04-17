"""Generate a small set of fully-synthetic sample cases for local testing.

These are NOT derived from any patient record. They exercise the rule
engine, guardrails, and response schema end-to-end.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def make_case(i: int) -> dict:
    t0 = datetime(2026, 4, 17, 6, 0, tzinfo=timezone.utc)
    variants = [
        dict(  # hyperK
            case_id=f"sample-{i:03d}-hyperK",
            demographics={"age_years": 72, "sex": "M", "weight_kg": 80},
            labs=[{"ts": _iso(t0 + timedelta(hours=2)), "name": "potassium", "value": 6.3, "unit": "mEq/L"}],
            medications=[],
            allergies=[],
        ),
        dict(  # PCN allergy + pip-tazo
            case_id=f"sample-{i:03d}-pcnAllergy",
            demographics={"age_years": 54, "sex": "F", "weight_kg": 65},
            labs=[],
            medications=[{"name": "piperacillin-tazobactam",
                          "start_ts": _iso(t0 + timedelta(hours=1)), "status": "active"}],
            allergies=[{"substance": "penicillin", "severity": "severe"}],
        ),
        dict(  # heparin no aPTT
            case_id=f"sample-{i:03d}-heparinNoAPTT",
            demographics={"age_years": 67, "sex": "M", "weight_kg": 85},
            labs=[],
            medications=[{"name": "heparin", "start_ts": _iso(t0 + timedelta(hours=1)),
                          "status": "active", "class": "anticoagulant"}],
            allergies=[],
        ),
    ]
    v = variants[i % len(variants)]
    return {
        **v,
        "encounter": {"encounter_id": f"E-{i}", "admission_ts": _iso(t0)},
        "icu_stay": {"stay_id": f"S-{i}", "icu_admit_ts": _iso(t0 + timedelta(minutes=30))},
        "vitals": [], "procedures": [], "devices": [],
        "diagnoses": [], "notes": [],
        "provenance": {"source": "synthetic", "extracted_ts": _iso(t0 + timedelta(hours=5))},
        "review_required": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/processed/samples")
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()
    outd = Path(args.out); outd.mkdir(parents=True, exist_ok=True)
    with (outd / "cases.jsonl").open("w", encoding="utf-8") as f:
        for i in range(args.n):
            case = make_case(i)
            rec = {"task": "icu_summary", "case": case, "target": {
                "summary": "Synthetic reference target; replace with clinician-curated narrative.",
                "active_problems": [], "alerts": [], "recommendations": [],
                "missing_data": ["clinician-curated narrative"],
                "uncertainty": "high", "escalation": "", "review_required": True, "evidence": [],
            }}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[samples] wrote {args.n} cases -> {outd / 'cases.jsonl'}")


if __name__ == "__main__":
    main()
