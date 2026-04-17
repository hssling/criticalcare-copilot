"""Run a benchmark suite and write JSON + Markdown reports.

Suites:
  * ``smoke``   — sample synthetic cases + a tiny red-team subset (CI-safe).
  * ``full``    — full internal test split.
  * ``red_team``— adversarial suite only.

Supports ``--mock``: skips model loading and returns a deterministic safe
abstention. This is how CI exercises the harness without a GPU.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.service import CopilotService
from safety import RuleEngine

from .metrics import (
    abstention_correctness, harmful_recommendation_rate, hallucinated_action_rate,
    med_conflict_recall, missed_monitoring_prf, red_flag_recall, schema_valid_rate,
)


class _MockClient:
    """Deterministic stub that always returns a safe abstention payload.
    Useful for CI and as a reference lower-bound."""
    def generate(self, *, case, task, evidence, system_prompt="", safety_prompt=""):
        return {
            "summary": "Mock run: no real model loaded; use clinician judgment.",
            "active_problems": [],
            "alerts": [],
            "recommendations": ["Review the case manually."],
            "missing_data": ["real model inference"],
            "uncertainty": "high",
            "escalation": "This is a mock response. Escalate to a clinician.",
            "review_required": True,
            "evidence": evidence[:3] if evidence else [],
            "abstained": True,
        }


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _suite_paths(suite: str) -> list[Path]:
    base = Path(__file__).parent
    if suite == "red_team":
        return [base / "custom_sets" / "red_team.jsonl"]
    if suite == "smoke":
        return [
            Path("data/processed/samples/cases.jsonl"),
            base / "custom_sets" / "red_team.jsonl",
        ]
    return [Path("data/processed/test.jsonl"),
            base / "custom_sets" / "red_team.jsonl"]


def run(suite: str, adapter: str | None, base: str | None, mock: bool) -> dict[str, Any]:
    if mock:
        client = _MockClient()
        model_version = "mock"
    else:
        # Intentionally lazy: only require torch if not in mock mode.
        from hf.endpoint_client import LocalHFClient  # type: ignore
        client = LocalHFClient(adapter=adapter, base=base)
        model_version = adapter or base or "unknown"

    service = CopilotService(
        rule_engine=RuleEngine(),
        retriever=None,
        model_client=client,
        model_version=model_version,
    )

    rows: list[dict] = []
    for p in _suite_paths(suite):
        rows.extend(_load_jsonl(p))

    preds: list[dict] = []
    targets: list[dict] = []
    for row in rows:
        pred = service.run(row["case"], task=row.get("task", "icu_summary"),
                           use_rag=False, use_model=True)
        preds.append(pred)
        targets.append(row.get("target", {}))

    p_mon, r_mon, f_mon = missed_monitoring_prf(preds, targets)

    report = {
        "suite": suite,
        "n": len(preds),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_version": model_version,
        "metrics": {
            "schema_valid_rate": schema_valid_rate(preds),
            "hallucinated_action_rate": hallucinated_action_rate(preds, targets),
            "harmful_recommendation_rate": harmful_recommendation_rate(preds),
            "abstention_correctness": abstention_correctness(preds, targets),
            "red_flag_recall": red_flag_recall(preds, targets),
            "med_conflict_recall": med_conflict_recall(preds, targets),
            "missed_monitoring_precision": p_mon,
            "missed_monitoring_recall": r_mon,
            "missed_monitoring_f1": f_mon,
        },
    }
    return report


def _regression_check(report: dict, baseline_path: Path) -> list[str]:
    failures: list[str] = []
    if not baseline_path.exists():
        return failures
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    m = report["metrics"]; b = baseline.get("metrics", {})
    # These must not regress
    if m["harmful_recommendation_rate"] > b.get("harmful_recommendation_rate", 0.0):
        failures.append(
            f"harmful_recommendation_rate regressed: {m['harmful_recommendation_rate']:.3f} > baseline {b.get('harmful_recommendation_rate', 0.0):.3f}")
    if m["hallucinated_action_rate"] > b.get("hallucinated_action_rate", 0.0):
        failures.append(
            f"hallucinated_action_rate regressed: {m['hallucinated_action_rate']:.3f} > baseline {b.get('hallucinated_action_rate', 0.0):.3f}")
    if m["schema_valid_rate"] + 1e-6 < b.get("schema_valid_rate", 1.0):
        failures.append(
            f"schema_valid_rate regressed: {m['schema_valid_rate']:.3f} < baseline {b.get('schema_valid_rate', 1.0):.3f}")
    if m["abstention_correctness"] + 1e-6 < b.get("abstention_correctness", 0.0):
        failures.append(
            f"abstention_correctness regressed: {m['abstention_correctness']:.3f} < baseline {b.get('abstention_correctness', 0.0):.3f}")
    if m["red_flag_recall"] + 1e-6 < b.get("red_flag_recall", 0.0):
        failures.append(
            f"red_flag_recall regressed: {m['red_flag_recall']:.3f} < baseline {b.get('red_flag_recall', 0.0):.3f}")
    if m["med_conflict_recall"] + 1e-6 < b.get("med_conflict_recall", 0.0):
        failures.append(
            f"med_conflict_recall regressed: {m['med_conflict_recall']:.3f} < baseline {b.get('med_conflict_recall', 0.0):.3f}")
    if m["missed_monitoring_f1"] + 1e-6 < b.get("missed_monitoring_f1", 0.0):
        failures.append(
            f"missed_monitoring_f1 regressed: {m['missed_monitoring_f1']:.3f} < baseline {b.get('missed_monitoring_f1', 0.0):.3f}")
    return failures


def _write_markdown(report: dict, path: Path) -> None:
    lines = [f"# Eval report — {report['suite']}",
             f"- n: {report['n']}",
             f"- model_version: {report['model_version']}",
             f"- timestamp: {report['timestamp']}", "", "| metric | value |", "|---|---|"]
    for k, v in report["metrics"].items():
        lines.append(f"| {k} | {v:.4f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="smoke", choices=["smoke", "full", "red_team"])
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--out", default="eval/reports/latest.json")
    ap.add_argument("--baseline", default="eval/baseline_metrics.json")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    report = run(args.suite, args.adapter, args.base, args.mock)
    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(report, outp.with_suffix(".md"))

    failures = _regression_check(report, Path(args.baseline))
    if failures:
        print("[eval] REGRESSION:")
        for f in failures:
            print(" -", f)
        raise SystemExit(2)
    print(f"[eval] wrote {outp} — all safety metrics within baseline.")


if __name__ == "__main__":
    main()
