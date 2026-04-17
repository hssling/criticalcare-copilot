# criticalcare-copilot

**Clinician-facing AI decision-support platform for critical care.**
_Review-required. Not autonomous. Not a replacement for physician judgment._

---

## ⚠️ Clinical Safety Disclaimer

This system is an **AI decision-support tool** intended to assist licensed critical-care clinicians. It is **not** a medical device, does **not** replace clinical judgment, and must **never** be used to autonomously diagnose, prescribe, or place orders. All outputs are marked `review_required: true` by default. See [docs/clinical-safety-scope.md](docs/clinical-safety-scope.md).

## Purpose

`criticalcare-copilot` helps ICU clinicians with:

1. **Case understanding** — summarization, active problem lists, trend interpretation, red-flag detection, handoff notes.
2. **Management assistance** — protocol-grounded checklists, monitoring suggestions, escalation triggers (never autonomous orders).
3. **Medical error alerting** — duplicate therapy, allergy conflicts, renal/hepatic dosing risks, missed monitoring, bundle omissions, ADE suspicion.

It combines:
- A **deterministic rule engine** (YAML-driven) that runs *before and alongside* the LLM.
- A fine-tuned **Gemma 4** model (E4B QLoRA first, 26B-A4B optional) with safety/abstention tuning.
- A **RAG layer** grounding outputs in local protocols and guidelines.
- A structured JSON **output contract** enforcing uncertainty, missing-data, review flags.

## Architecture

```
 ┌──────────────────────────────────────────────────────────────┐
 │                   Clinician Browser (Netlify)                │
 │         React + TS UI · no secrets · accessible              │
 └───────────────┬──────────────────────────────────┬───────────┘
                 │ HTTPS                            │
                 ▼                                  ▼
        ┌────────────────────┐          ┌───────────────────┐
        │ Netlify Functions  │◀────────▶│  Audit log store  │
        │ infer · safety     │          │  (pluggable)      │
        │ retrieve · health  │          └───────────────────┘
        └─────┬───────┬──────┘
              │       │
              │       └──────────▶ RAG retriever (FAISS, pluggable)
              ▼
    ┌──────────────────────┐        ┌─────────────────────────┐
    │ Deterministic Rules  │───────▶│   Merged response       │
    │ (YAML packs)         │        │   (schema-validated)    │
    └──────────┬───────────┘        └──────────┬──────────────┘
               │                               │
               ▼                               ▼
    ┌──────────────────────┐        ┌─────────────────────────┐
    │ HF Inference Endpoint│        │   Model Card / Eval     │
    │ Gemma 4 fine-tuned   │        │   Artifacts             │
    └──────────────────────┘        └─────────────────────────┘
```

## Repo map

| Path | Purpose |
|------|---------|
| `docs/` | Product spec, safety scope, governance, model card, validation, deployment |
| `data/schemas/` | JSON Schemas for case / alert / response |
| `data/builders/` | Dataset ingestion (MIMIC-IV, eICU, n2c2, safety pairs) |
| `training/` | SFT + DPO configs, prompts, scripts, Kaggle notebooks |
| `eval/` | Benchmark runner, metrics, rubrics, baseline regression |
| `rules/` | YAML rule packs (dosing, allergy, prophylaxis, monitoring) |
| `safety/` | Rule engine, schema validation, guardrails |
| `rag/` | Ingestion, chunking, embeddings, retriever |
| `api/` | Pydantic request/response, service orchestration |
| `app/frontend/` | React + TS clinician UI |
| `app/functions/` | Netlify Functions (TS) inference proxy |
| `hf/` | HF publishing, Space app, endpoint client |
| `scripts/` | Bootstrap, local API, validators, sample data |
| `tests/` | Unit tests |
| `.github/workflows/` | CI, eval regression, deploy |

## Quickstart

```bash
# Python side
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python scripts/generate_sample_cases.py
python scripts/validate_data.py
pytest tests/

# Local API
python scripts/run_local_api.py  # uvicorn on :8000

# Frontend
cd app/frontend
npm install
npm run dev
```

Configuration: copy `.env.example` → `.env` and fill values. **Never commit `.env`.**

## Training overview

1. Build normalized JSONL datasets: `python -m data.builders.build_mimic_cases --config …`
2. SFT Gemma 4 E4B with QLoRA: `python training/scripts/train_sft.py --config training/configs/gemma4_e4b_qlora.yaml`
3. Optional DPO on safety pairs: `python training/scripts/train_dpo.py …`
4. Export adapters / merge: `python training/scripts/merge_lora.py …`
5. Publish to HF: `python hf/publish_model.py …`

See [docs/kaggle-workflow.md](docs/kaggle-workflow.md).

## Evaluation overview

- ICU rubric scoring, medication-safety P/R, abstention correctness, hallucination rate.
- MedQA / MedMCQA / PubMedQA comparator runs.
- External validation on eICU split.
- Regression gate against `eval/baseline_metrics.json` enforced in CI.

See [docs/validation-plan.md](docs/validation-plan.md).

## Deployment overview

- **Model**: Hugging Face Inference Endpoint (private).
- **API relay**: Netlify Functions (secrets in function env only, never in `netlify.toml`).
- **Frontend**: Netlify static hosting.
- **Demo**: HF Space.

See [docs/deployment-architecture.md](docs/deployment-architecture.md) and [docs/netlify-setup.md](docs/netlify-setup.md).

## License

See [LICENSE](LICENSE). Clinical use governed by [docs/release-gating.md](docs/release-gating.md).
