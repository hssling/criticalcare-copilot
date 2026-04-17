"""Deterministic train/valid/test split over one or more JSONL input files.

- Hash-based split on ``case.case_id`` so the same record always lands in
  the same split regardless of file order.
- Optional ``--holdout-source`` reserves an entire source (e.g., ``eicu-crd``)
  as an external validation split written to ``external.jsonl``.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path


def _bucket(key: str) -> str:
    h = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16)
    p = h % 100
    if p < 85:
        return "train"
    if p < 95:
        return "valid"
    return "test"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True, help="Glob(s) of input JSONL files.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--holdout-source", default=None)
    args = ap.parse_args()

    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    fhs = {name: (outdir / f"{name}.jsonl").open("w", encoding="utf-8")
           for name in ("train", "valid", "test", "external")}

    counts = {"train": 0, "valid": 0, "test": 0, "external": 0}
    paths: list[str] = []
    for g in args.inputs:
        paths.extend(glob.glob(g))
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                src = rec.get("case", {}).get("provenance", {}).get("source", "")
                if args.holdout_source and src == args.holdout_source:
                    fhs["external"].write(line + "\n"); counts["external"] += 1
                    continue
                cid = rec.get("case", {}).get("case_id", line[:64])
                b = _bucket(cid)
                fhs[b].write(line + "\n"); counts[b] += 1

    for fh in fhs.values():
        fh.close()
    print(f"[split] counts={counts} -> {outdir}")


if __name__ == "__main__":
    main()
