"""DPO on preference pairs produced by ``data/builders/build_safety_pairs.py``.

Each pair has:
  { "prompt": "...", "chosen": "...", "rejected": "..." }

Example:
    python training/scripts/train_dpo.py --config training/configs/gemma4_e4b_qlora.yaml \
        --pairs data/processed/safety_pairs.jsonl --out checkpoints/gemma4_e4b_dpo
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--adapter", default=None, help="Path to SFT-tuned adapter to start from.")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    import torch
    from datasets import Dataset
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import DPOConfig, DPOTrainer

    tok = AutoTokenizer.from_pretrained(cfg["model"]["base"], use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_use_double_quant=True,
                             bnb_4bit_compute_dtype=torch.bfloat16)
    base = AutoModelForCausalLM.from_pretrained(
        cfg["model"]["base"], quantization_config=bnb, torch_dtype=torch.bfloat16,
    )
    model = PeftModel.from_pretrained(base, args.adapter) if args.adapter else base

    rows = _load_jsonl(Path(args.pairs))
    ds = Dataset.from_list(rows)

    dpo_cfg = DPOConfig(
        output_dir=args.out,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=5e-6,
        num_train_epochs=1,
        beta=0.1,
        max_length=cfg["data"].get("max_seq_len", 2048),
        max_prompt_length=1024,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=10,
        save_steps=200,
        report_to=[],
    )
    trainer = DPOTrainer(model=model, args=dpo_cfg, train_dataset=ds, tokenizer=tok)
    trainer.train()
    trainer.save_model(args.out)
    tok.save_pretrained(args.out)
    print(f"[train_dpo] saved to {args.out}")


if __name__ == "__main__":
    main()
