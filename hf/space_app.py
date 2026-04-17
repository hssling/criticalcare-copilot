"""Minimal Gradio Space demo for criticalcare-copilot.

Displays a prominent clinical disclaimer, a case picker, and the
structured response. Uses the Python service so rules + retrieval + model
all run in the Space. For production use the Netlify UI instead.
"""
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from api.service import CopilotService

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "data" / "processed" / "samples"
SERVICE = CopilotService()

DISCLAIMER = (
    "⚠️ **Clinician-facing demo.** This tool is review-required and not a replacement "
    "for clinical judgment. Do **not** paste real PHI."
)


def _samples() -> list[str]:
    f = SAMPLES_DIR / "cases.jsonl"
    if not f.exists():
        return []
    ids = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            ids.append(json.loads(line)["case"]["case_id"])
        except Exception:
            continue
    return ids


def _load_sample(case_id: str) -> str:
    f = SAMPLES_DIR / "cases.jsonl"
    for line in f.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec["case"]["case_id"] == case_id:
            return json.dumps(rec["case"], indent=2)
    return "{}"


def _infer(case_json: str, task: str) -> str:
    try:
        case = json.loads(case_json)
    except Exception as e:
        return json.dumps({"error": f"invalid JSON: {e}"}, indent=2)
    return json.dumps(SERVICE.run(case, task=task), indent=2)


with gr.Blocks(title="criticalcare-copilot demo") as demo:
    gr.Markdown(DISCLAIMER)
    with gr.Row():
        task = gr.Dropdown(
            ["icu_summary", "management_assistance", "medication_safety", "handoff_generation"],
            value="icu_summary", label="Task",
        )
        sample = gr.Dropdown(_samples(), value=None, label="Sample case")
    case_box = gr.Code(label="Case JSON", language="json", lines=20)
    out_box = gr.Code(label="Response JSON", language="json", lines=25)
    sample.change(_load_sample, inputs=[sample], outputs=[case_box])
    btn = gr.Button("Run", variant="primary")
    btn.click(_infer, inputs=[case_box, task], outputs=[out_box])


if __name__ == "__main__":
    demo.launch()
