"""Build medication-safety training records from n2c2 ADE-style corpora.

Expects ``$N2C2_ADE_ROOT`` with Brat-style annotation (.ann + .txt) files.
If not present, exits 0 after writing no records.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _read_pair(txt_path: Path) -> tuple[str, list[str]]:
    ann_path = txt_path.with_suffix(".ann")
    text = txt_path.read_text(encoding="utf-8", errors="ignore")
    labels: list[str] = []
    if ann_path.exists():
        for line in ann_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and parts[0].startswith("T"):
                span_info = parts[1].split()
                if span_info and span_info[0] in {"Drug", "ADE", "Reason", "Dose", "Route"}:
                    labels.append(f"{span_info[0]}: {parts[2].strip()}")
    return text, labels


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = os.getenv("N2C2_ADE_ROOT")
    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w", encoding="utf-8") as f:
        if root and Path(root).exists():
            for txt in Path(root).rglob("*.txt"):
                text, labels = _read_pair(txt)
                rec = {
                    "task": "medication_safety",
                    "case": {
                        "case_id": f"n2c2-{txt.stem}",
                        "demographics": {"age_years": 0, "sex": "unknown"},
                        "encounter": {"encounter_id": txt.stem, "admission_ts": "1970-01-01T00:00:00Z"},
                        "icu_stay": {"stay_id": txt.stem, "icu_admit_ts": "1970-01-01T00:00:00Z"},
                        "notes": [{"ts": "1970-01-01T00:00:00Z", "kind": "discharge", "text": text}],
                        "provenance": {"source": "n2c2-ade", "extracted_ts": "1970-01-01T00:00:00Z"},
                        "review_required": True,
                    },
                    "target": {
                        "summary": "Medication-safety review of an annotated discharge summary.",
                        "active_problems": [],
                        "alerts": [],
                        "recommendations": [f"Review annotation: {l}" for l in labels[:10]],
                        "missing_data": [],
                        "uncertainty": "medium",
                        "escalation": "",
                        "review_required": True,
                        "evidence": [],
                    },
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    print(f"[build_n2c2_ade_cases] wrote {n} records -> {outp}")


if __name__ == "__main__":
    main()
