#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python scripts/generate_sample_cases.py --out data/processed/samples --n 5
python scripts/validate_data.py --dir data/processed/samples
(cd app/frontend && npm install)
(cd app/functions && npm install)
echo "Bootstrap complete."
