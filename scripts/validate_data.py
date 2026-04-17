"""Validate every .jsonl file under a directory against case_schema.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from safety.schema_validation import validate_case


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    d = Path(args.dir)
    ok = 0
    bad = 0
    for f in d.rglob("*.jsonl"):
        with f.open("r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                case = rec.get("case", rec)
                errs = validate_case(case)
                if errs:
                    bad += 1
                    print(f"[INVALID] {f}:{i} — {errs[0]}")
                else:
                    ok += 1
    print(f"[validate] ok={ok} bad={bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
