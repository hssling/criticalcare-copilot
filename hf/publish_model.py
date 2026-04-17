"""Publish a local model directory (adapter or merged) to the HF Hub.

Writes a README.md generated from ``docs/model-card-template.md`` and
``eval/reports/latest.json`` before upload.

Example:
    python hf/publish_model.py --path checkpoints/merged --repo $HF_ORG/$HF_MODEL_REPO
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Local model directory to push.")
    ap.add_argument("--repo", required=True, help="HF repo id, e.g. org/name.")
    ap.add_argument("--private", action="store_true", default=True)
    args = ap.parse_args()

    from huggingface_hub import HfApi, create_repo

    from hf.generate_model_card import generate_card

    token = os.getenv("HF_HUB_TOKEN")
    if not token:
        raise SystemExit("HF_HUB_TOKEN not set")

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"no such path: {path}")

    card = generate_card()
    (path / "README.md").write_text(card, encoding="utf-8")

    # Copy relevant eval artifacts alongside the model
    latest = Path("eval/reports/latest.json")
    if latest.exists():
        shutil.copy2(latest, path / "eval_report.json")

    create_repo(repo_id=args.repo, token=token, private=args.private, exist_ok=True)
    api = HfApi(token=token)
    api.upload_folder(folder_path=str(path), repo_id=args.repo, repo_type="model",
                      commit_message="criticalcare-copilot upload")
    print(f"[publish_model] uploaded {path} -> {args.repo}")


if __name__ == "__main__":
    main()
