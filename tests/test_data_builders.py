"""Smoke tests for builders — ensure they run cleanly even with no mounted data."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_safety_pairs_builder_writes_records(tmp_path: Path):
    out = tmp_path / "pairs.jsonl"
    cp = subprocess.run([sys.executable, "-m", "data.builders.build_safety_pairs", "--out", str(out)],
                        capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows
    assert all({"prompt", "chosen", "rejected"} <= r.keys() for r in rows)


def test_mimic_builder_exits_clean_without_data(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("MIMIC_IV_ROOT", raising=False)
    out = tmp_path / "m.jsonl"
    cp = subprocess.run([sys.executable, "-m", "data.builders.build_mimic_cases", "--out", str(out)],
                        capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr
    # With no data mounted, the file exists but may be empty — that's fine.
    assert out.exists()
