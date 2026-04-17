# Local Development

## Prerequisites
- Python 3.11+
- Node 20+
- (optional) CUDA GPU for training

## Bootstrap
```bash
# From repo root
bash scripts/bootstrap.sh      # macOS / Linux
# or
powershell scripts/bootstrap.ps1   # Windows
```

This creates the venv, installs Python + Node deps, and generates sample synthetic cases under `data/processed/samples/`.

## Run tests
```bash
pytest tests/
```

## Run local API
```bash
python scripts/run_local_api.py
# -> http://127.0.0.1:8000/docs
```

The local API exposes the same surface as Netlify Functions, backed by the Python service for debugging.

## Run frontend
```bash
cd app/frontend
npm install
npm run dev
```

By default `VITE_FUNCTIONS_BASE` points at Netlify Functions. Override to point at the local FastAPI during development:

```
# app/frontend/.env.local
VITE_FUNCTIONS_BASE=http://127.0.0.1:8000/api
```

## Run everything together with Netlify dev
```bash
netlify dev
```

## Regenerate sample data
```bash
python scripts/generate_sample_cases.py --out data/processed/samples --n 10
python scripts/validate_data.py --dir data/processed/samples
```
