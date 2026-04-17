"""Run the benchmark harness against a local adapter/checkpoint.

Thin wrapper around ``eval.benchmark_runner``. The runner supports a
``--mock`` mode that skips model loading and uses a deterministic stub —
useful in CI.
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--suite", default="smoke", choices=["smoke", "full", "red_team"])
    ap.add_argument("--out", default="eval/reports/latest.json")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    cmd = [sys.executable, "-m", "eval.benchmark_runner",
           "--suite", args.suite, "--out", args.out]
    if args.adapter:
        cmd += ["--adapter", args.adapter]
    if args.base:
        cmd += ["--base", args.base]
    if args.mock:
        cmd += ["--mock"]
    print("$", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
