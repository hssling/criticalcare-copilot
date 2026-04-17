# Deployment Architecture

```
 ┌──────────────┐   HTTPS   ┌───────────────────────┐
 │  Clinician   │──────────▶│ Netlify CDN (frontend)│
 │  browser     │           │ React + TS SPA        │
 └──────┬───────┘           └──────────┬────────────┘
        │                              │ fetch('/.netlify/functions/…')
        │                              ▼
        │                  ┌───────────────────────────┐
        │                  │  Netlify Functions (Node) │
        │                  │  infer · safety · health  │
        │                  │  retrieve · audit_log     │
        │                  └───────────┬───────────────┘
        │                              │ HTTPS + Bearer
        │                              ▼
        │              ┌──────────────────────────────────┐
        │              │ HF Inference Endpoint (private)  │
        │              │ Gemma-4 fine-tuned + adapter     │
        │              └──────────────────────────────────┘
        │                              │
        │                              ▼
        │              ┌──────────────────────────────────┐
        │              │ Rule engine (in-function)        │
        │              │ RAG retriever (FAISS, loaded     │
        │              │ from processed artifacts bundle) │
        │              └──────────────────────────────────┘
        ▼
 ┌────────────────────────────────────────────────────────┐
 │ Audit log sink (pluggable): file / Blob / DB — config  │
 └────────────────────────────────────────────────────────┘
```

## Why this split
- **Frontend on Netlify**: CDN-cached, no secret exposure, preview URLs per PR.
- **Functions for secrets**: HF tokens never reach the browser.
- **HF Endpoint for compute**: no custom GPU infra; easy model version swap via env var.
- **Local rule engine**: deterministic safety runs even if the model endpoint is degraded.

## Environments
- **Dev**: local Vite + `netlify dev` + mock HF client.
- **Staging (Netlify preview)**: auto-deployed per PR, points at a staging HF endpoint.
- **Prod**: Netlify production domain, production HF endpoint, audit log sink enabled.

## Secrets
- Stored in Netlify UI (Site → Environment variables).
- Never in `netlify.toml`, never in git, never sent to the browser.
- See `.env.example` for the expected variable set.

## Failure modes
- HF endpoint down → functions return rules-only response with `review_required=true` and `escalation` populated.
- Schema validation fails → safety event logged, user sees a neutral error; no partial/unsafe output is rendered.
- Rate limit → exponential backoff in `hf/endpoint_client.py`.
