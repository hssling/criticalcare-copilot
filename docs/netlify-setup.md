# Netlify Setup

## One-time
1. Create a new Netlify site linked to the GitHub repo.
2. Build settings (auto-detected from `netlify.toml`):
   - Base directory: `app/frontend`
   - Publish directory: `app/frontend/dist`
   - Functions directory: `app/functions`
3. **Environment variables** (Site → Settings → Environment variables). Use values from `.env.example` as the shape:
   - `HF_ENDPOINT_URL`
   - `HF_API_TOKEN` (mark as sensitive)
   - `HF_MODEL_REVISION`
   - `VECTOR_STORE_PATH` (if shipping a RAG bundle with functions)
   - `AUDIT_LOG_PATH` (or an external sink URL)
   - `ENABLE_MODEL_CALL`, `ENABLE_RAG`, `SAFETY_STRICT_MODE`
4. Do **not** put any of these in `netlify.toml`.

## Local dev
```bash
npm install -g netlify-cli
netlify link
netlify dev        # proxies Vite + Functions together
```

Create `app/frontend/.env.local` with non-secret `VITE_*` vars only.

## Previews
Each PR gets a preview URL. Preview deploys can point to a **staging** HF endpoint by using Netlify's per-branch env override.

## Rollback
Netlify Deploys → select previous → "Publish deploy".

## Health
`/.netlify/functions/health` returns `{ok: true, model_endpoint: "reachable"|"unreachable"}`; frontend polls on load.
