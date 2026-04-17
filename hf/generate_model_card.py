"""Render ``docs/model-card-template.md`` into a final model card
using ``eval/reports/latest.json`` values (or sensible placeholders).
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TEMPLATE = Path("docs/model-card-template.md")
REPORT = Path("eval/reports/latest.json")


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def generate_card() -> str:
    if not TEMPLATE.exists():
        return "# Model Card\n\n(template missing)\n"
    text = TEMPLATE.read_text(encoding="utf-8")
    metrics: dict = {}
    version = os.getenv("HF_MODEL_REVISION", "dev")
    if REPORT.exists():
        r = json.loads(REPORT.read_text(encoding="utf-8"))
        metrics = r.get("metrics", {})
        version = r.get("model_version", version)
    replacements = {
        "{{model_version}}": version,
        "{{version}}": version,
        "{{git_sha}}": _git_sha(),
        "{{release_date}}": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "{{icu_rubric}}": "TBD",
        "{{icu_rubric_baseline}}": "TBD",
        "{{Δ}}": "TBD",
        "{{red_flag_recall}}": f"{metrics.get('red_flag_recall', 'TBD')}",
        "{{med_conflict_recall}}": f"{metrics.get('med_conflict_recall', 'TBD')}",
        "{{halluc_rate}}": f"{metrics.get('hallucinated_action_rate', 'TBD')}",
        "{{abstention_acc}}": f"{metrics.get('abstention_correctness', 'TBD')}",
        "{{medqa}}": "TBD",
        "{{medmcqa}}": "TBD",
        "{{pubmedqa}}": "TBD",
    }
    for k, v in replacements.items():
        text = text.replace(k, str(v))
    return text


if __name__ == "__main__":
    print(generate_card())
