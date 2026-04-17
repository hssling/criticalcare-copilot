"""Augment MIMIC cases with de-identified notes (MIMIC-IV-Note).

Joins notes to the cases produced by ``build_mimic_cases`` by ``hadm_id``.
Expects ``$MIMIC_IV_NOTE_ROOT`` to point at a folder containing
``discharge.csv.gz`` / ``radiology.csv.gz`` etc. If not mounted, no-ops.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-notes", type=int, default=10)
    args = ap.parse_args()

    root = os.getenv("MIMIC_IV_NOTE_ROOT")
    notes_by_hadm: dict[str, list[dict]] = {}
    if root and Path(root).exists():
        import pandas as pd
        for kind, fname in (("discharge", "discharge.csv.gz"), ("radiology", "radiology.csv.gz")):
            p = Path(root) / fname
            if not p.exists():
                continue
            df = pd.read_csv(p, usecols=["hadm_id", "charttime", "text"])
            for hadm, grp in df.groupby("hadm_id"):
                notes_by_hadm.setdefault(str(hadm), []).extend(
                    {"ts": str(r["charttime"]), "kind": kind, "text": str(r["text"])}
                    for _, r in grp.head(args.max_notes).iterrows()
                )

    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with Path(args.inp).open("r", encoding="utf-8") as fin, outp.open("w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line)
            hadm = rec["case"]["encounter"]["encounter_id"]
            rec["case"]["notes"] = notes_by_hadm.get(hadm, [])[: args.max_notes]
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"[build_mimic_notes_cases] wrote {n} records -> {outp}")


if __name__ == "__main__":
    main()
