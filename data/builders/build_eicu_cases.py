"""Build normalized ICU cases from eICU-CRD. Mirrors build_mimic_cases.py.

Expects ``$EICU_ROOT`` with standard layout. Used both for training and
as an external validation split (see data/builders/split_train_valid_test).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

from safety.schema_validation import validate_case


def iter_cases(limit: int | None = None) -> Iterable[dict]:
    root = os.getenv("EICU_ROOT")
    if not root or not Path(root).exists():
        return
    import pandas as pd
    pat = Path(root) / "patient.csv.gz"
    if not pat.exists():
        pat = Path(root) / "patient.csv"
    if not pat.exists():
        return
    df = pd.read_csv(pat)
    if limit:
        df = df.head(limit)
    for _, r in df.iterrows():
        sex = (r.get("gender") or "unknown").strip()
        sex = "M" if sex.lower().startswith("m") else "F" if sex.lower().startswith("f") else "unknown"
        age = str(r.get("age") or "").replace(">", "").replace("<", "").strip()
        try:
            age_years = float(age) if age else 0.0
        except ValueError:
            age_years = 0.0
        case = {
            "case_id": f"eicu-{r['patientunitstayid']}",
            "demographics": {
                "age_years": age_years,
                "sex": sex,
                "weight_kg": float(r["admissionweight"]) if pd.notna(r.get("admissionweight")) else None,
                "height_cm": float(r["admissionheight"]) if pd.notna(r.get("admissionheight")) else None,
            },
            "encounter": {
                "encounter_id": str(r.get("patienthealthsystemstayid", r["patientunitstayid"])),
                "admission_ts": "1970-01-01T00:00:00Z",
            },
            "icu_stay": {
                "stay_id": str(r["patientunitstayid"]),
                "icu_admit_ts": "1970-01-01T00:00:00Z",
                "unit_type": r.get("unittype"),
            },
            "vitals": [], "labs": [], "medications": [],
            "procedures": [], "devices": [], "allergies": [],
            "diagnoses": [], "notes": [],
            "provenance": {
                "source": "eicu-crd", "source_version": "2.0",
                "extracted_ts": "1970-01-01T00:00:00Z",
                "deidentified": True,
            },
            "review_required": True,
        }
        if validate_case(case):
            continue
        yield {"task": "icu_summary", "case": case, "target": {
            "summary": "Placeholder — awaiting curation.",
            "active_problems": [],
            "alerts": [], "recommendations": [], "missing_data": ["curated narrative"],
            "uncertainty": "high", "escalation": "", "review_required": True, "evidence": [],
        }}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w", encoding="utf-8") as f:
        for rec in iter_cases(limit=args.limit):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"[build_eicu_cases] wrote {n} records -> {outp}")


if __name__ == "__main__":
    main()
