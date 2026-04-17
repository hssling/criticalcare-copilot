$ErrorActionPreference = "Stop"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
python scripts/generate_sample_cases.py --out data/processed/samples --n 5
python scripts/validate_data.py --dir data/processed/samples
Push-Location app/frontend ; npm install ; Pop-Location
Push-Location app/functions ; npm install ; Pop-Location
Write-Host "Bootstrap complete."
