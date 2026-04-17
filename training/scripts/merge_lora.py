"""Merge a LoRA/QLoRA adapter into the base model and save a full checkpoint.

Example:
    python training/scripts/merge_lora.py \
        --base google/gemma-4-e4b-it \
        --adapter checkpoints/gemma4_e4b_qlora \
        --out checkpoints/gemma4_e4b_merged
"""
from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(args.base, use_fast=True)
    base = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16)
    model = PeftModel.from_pretrained(base, args.adapter)
    merged = model.merge_and_unload()
    merged.save_pretrained(args.out, safe_serialization=True)
    tok.save_pretrained(args.out)
    print(f"[merge_lora] merged -> {args.out}")


if __name__ == "__main__":
    main()
