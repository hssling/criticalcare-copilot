"""Build normalized ICU cases from MIMIC-IV.

**This script expects MIMIC-IV to be locally available** at
``$MIMIC_IV_ROOT`` with the standard PhysioNet layout (``hosp/``,
``icu/``). It reads CSV/CSV.GZ tables lazily and emits JSONL records
conforming to ``data/schemas/case_schema.json``.

If MIMIC-IV is not mounted, the script writes zero records and exits 0 —
useful in CI.

Example:
    python -m data.builders.build_mimic_cases --out data/interim/mimic_cases.jsonl --limit 1000
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

from safety.schema_validation import validate_case


def _root() -> Path | None:
    p = os.getenv("MIMIC_IV_ROOT")
    return Path(p) if p and Path(p).exists() else None


def _read_csv(path: Path, **kw):
    import pandas as pd
    return pd.read_csv(path, **kw)


def iter_cases(limit: int | None = None) -> Iterable[dict]:
    root = _root()
    if root is None:
        return
    # Pandas is imported lazily to keep CI light.
    import pandas as pd

    hosp = root / "hosp"
    icu = root / "icu"
    if not (hosp.exists() and icu.exists()):
        return

    pats = _read_csv(hosp / "patients.csv.gz") if (hosp / "patients.csv.gz").exists() \
        else _read_csv(hosp / "patients.csv")
    adm  = _read_csv(hosp / "admissions.csv.gz") if (hosp / "admissions.csv.gz").exists() \
        else _read_csv(hosp / "admissions.csv")
    stays = _read_csv(icu / "icustays.csv.gz") if (icu / "icustays.csv.gz").exists() \
        else _read_csv(icu / "icustays.csv")

    merged = stays.merge(adm, on=["subject_id", "hadm_id"], how="left") \
                  .merge(pats, on="subject_id", how="left")
    if limit:
        merged = merged.head(limit)

    for _, row in merged.iterrows():
        sex = str(row.get("gender") or "unknown")[:1]
        case = {
            "case_id": f"mimic4-{row['stay_id']}",
            "demographics": {
                "age_years": float(row.get("anchor_age") or 0),
                "sex": sex if sex in ("M", "F") else "unknown",
                "weight_kg": None,
                "height_cm": None,
            },
            "encounter": {
                "encounter_id": str(row["hadm_id"]),
                "admission_ts": str(row.get("admittime")),
                "discharge_ts": str(row.get("dischtime")) if pd.notna(row.get("dischtime")) else None,
                "admit_source": row.get("admission_location"),
            },
            "icu_stay": {
                "stay_id": str(row["stay_id"]),
                "icu_admit_ts": str(row.get("intime")),
                "icu_discharge_ts": str(row.get("outtime")) if pd.notna(row.get("outtime")) else None,
                "unit_type": row.get("first_careunit"),
            },
            "vitals": [], "labs": [], "medications": [],
            "procedures": [], "devices": [], "allergies": [],
            "diagnoses": [], "notes": [],
            "provenance": {
                "source": "mimic-iv", "source_version": "2.x",
                "extracted_ts": "1970-01-01T00:00:00Z",
                "deidentified": True,
            },
            "review_required": True,
        }
        errs = validate_case(case)
        if errs:
            # Skip records that cannot be normalized; do not fail the whole build.
            continue
        yield {"task": "icu_summary", "case": case, "target": _default_target(case)}


def _default_target(case: dict) -> dict:
    dxs = [d.get("label", "") for d in case.get("diagnoses", [])[:5]]
    return {
        "summary": "Placeholder summary — replace with clinician-curated target during labeling.",
        "active_problems": dxs,
        "alerts": [],
        "recommendations": ["Review handoff completeness with bedside team."],
        "missing_data": ["clinician-curated narrative"],
        "uncertainty": "high",
        "escalation": "",
        "review_required": True,
        "evidence": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as f:
        for rec in iter_cases(limit=args.limit):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"[build_mimic_cases] wrote {n} records -> {out}")


if __name__ == "__main__":
    main()
