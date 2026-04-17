"""Supervised fine-tuning (QLoRA) entry point.

Reads a YAML config like ``training/configs/gemma4_e4b_qlora.yaml`` and runs
QLoRA SFT with TRL ``SFTTrainer``. Writes the adapter to ``training.output_dir``.

Heavy deps (torch/transformers/peft/trl/bitsandbytes) are imported lazily so
this file is importable in CI without GPU deps installed.

Example:
    python training/scripts/train_sft.py --config training/configs/gemma4_e4b_qlora.yaml
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def _load_jsonl(path: str | Path) -> list[dict]:
    out = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _format_example(ex: dict, system_prompt: str, safety_prompt: str) -> str:
    """Concatenate system + safety + user + assistant target into one string.

    Expected example shape:
      { "task": str, "case": {...}, "target": {... response json ...} }
    """
    user = {
        "task": ex.get("task", "icu_summary"),
        "case": ex.get("case", {}),
        "evidence": ex.get("evidence", []),
    }
    return (
        f"<|system|>\n{system_prompt}\n\n{safety_prompt}\n"
        f"<|user|>\n{json.dumps(user, ensure_ascii=False)}\n"
        f"<|assistant|>\n{json.dumps(ex['target'], ensure_ascii=False)}\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Lazy heavy imports
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments,
    )
    from trl import SFTTrainer

    # --- Tokenizer ---
    tok_cfg = cfg.get("tokenizer", {})
    tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["base"], use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.model_max_length = tok_cfg.get("model_max_length", 2048)

    # --- Model ---
    qcfg = cfg["model"].get("quantization", {})
    bnb = BitsAndBytesConfig(
        load_in_4bit=qcfg.get("enabled", True),
        bnb_4bit_quant_type=qcfg.get("type", "nf4"),
        bnb_4bit_use_double_quant=qcfg.get("double_quant", True),
        bnb_4bit_compute_dtype=torch.bfloat16,
    ) if qcfg.get("enabled", True) else None

    model = AutoModelForCausalLM.from_pretrained(
        cfg["model"]["base"],
        quantization_config=bnb,
        torch_dtype=torch.bfloat16,
        attn_implementation=cfg["model"].get("attn_implementation", "sdpa"),
    )
    model = prepare_model_for_kbit_training(model) if bnb else model

    lora = cfg["lora"]
    peft_config = LoraConfig(
        r=lora["r"], lora_alpha=lora["alpha"], lora_dropout=lora["dropout"],
        bias=lora.get("bias", "none"), target_modules=lora["target_modules"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # --- Data ---
    d = cfg["data"]
    sys_p = Path(d["prompt_template"]).read_text(encoding="utf-8")
    safety_p = Path(d["safety_prompt"]).read_text(encoding="utf-8")

    train_rows = _load_jsonl(d["train_path"])
    valid_rows = _load_jsonl(d["valid_path"]) if Path(d["valid_path"]).exists() else []

    train_texts = [_format_example(r, sys_p, safety_p) for r in train_rows]
    valid_texts = [_format_example(r, sys_p, safety_p) for r in valid_rows]

    train_ds = Dataset.from_dict({"text": train_texts})
    valid_ds = Dataset.from_dict({"text": valid_texts}) if valid_texts else None

    # --- Training ---
    t = cfg["training"]
    targs = TrainingArguments(
        output_dir=t["output_dir"],
        per_device_train_batch_size=t["per_device_train_batch_size"],
        per_device_eval_batch_size=t["per_device_eval_batch_size"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=t["learning_rate"],
        lr_scheduler_type=t["lr_scheduler_type"],
        warmup_ratio=t["warmup_ratio"],
        num_train_epochs=t["num_train_epochs"],
        logging_steps=t["logging_steps"],
        save_steps=t["save_steps"],
        eval_steps=t["eval_steps"] if valid_ds else None,
        eval_strategy="steps" if valid_ds else "no",
        save_total_limit=t["save_total_limit"],
        bf16=t.get("bf16", True),
        gradient_checkpointing=t.get("gradient_checkpointing", True),
        optim=t.get("optim", "paged_adamw_8bit"),
        weight_decay=t.get("weight_decay", 0.0),
        max_grad_norm=t.get("max_grad_norm", 1.0),
        seed=t.get("seed", 1337),
        report_to=t.get("report_to", []),
    )

    trainer = SFTTrainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        tokenizer=tokenizer,
        dataset_text_field="text",
        max_seq_length=d.get("max_seq_len", 2048),
        packing=d.get("pack", False),
    )

    trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(t["output_dir"])
    tokenizer.save_pretrained(t["output_dir"])
    print(f"[train_sft] saved to {t['output_dir']}")


if __name__ == "__main__":
    main()
