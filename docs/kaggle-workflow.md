# Kaggle Workflow

Kaggle notebooks live in `training/kaggle/`.

## Expected Kaggle inputs
Attach (via Kaggle "Add data"):
- `mimic-iv` (credentialed)
- `mimic-iv-note` (credentialed)
- `eicu-crd` (credentialed)
- `n2c2-ade` (if available)

They mount under `/kaggle/input/<slug>/…`. Set env vars at notebook top:

```python
import os
os.environ["MIMIC_IV_ROOT"] = "/kaggle/input/mimic-iv"
os.environ["MIMIC_IV_NOTE_ROOT"] = "/kaggle/input/mimic-iv-note"
os.environ["EICU_ROOT"] = "/kaggle/input/eicu-crd"
os.environ["N2C2_ADE_ROOT"] = "/kaggle/input/n2c2-ade"
```

## Notebook order
1. `kaggle_01_eda.ipynb` — inspect mounted inputs, counts, missingness.
2. `kaggle_02_dataset_build.ipynb` — run `data/builders/*` to produce JSONL in `/kaggle/working/processed/`.
3. `kaggle_03_train_gemma4_e4b.ipynb` — QLoRA SFT; writes adapter to `/kaggle/working/checkpoints/`.
4. `kaggle_04_eval.ipynb` — evaluation harness subset + regression report.
5. `kaggle_05_export_hf.ipynb` — push adapter + model card to HF Hub.

## Memory guidance (Kaggle T4 x2)
- Use `training/configs/gemma4_e4b_qlora.yaml` (batch 1, grad-accum 16, seq 2048, bf16).
- `bitsandbytes` 4-bit NF4 quantization.
- Enable gradient checkpointing.
- Offload optimizer state if OOM: set `optim: paged_adamw_8bit`.

## Resume training
Checkpoints saved every `save_steps`. Re-run notebook; script detects `resume_from_checkpoint` automatically if `/kaggle/working/checkpoints/last/` exists.

## Metrics tracking
Script logs to `trl`/`transformers` trainer state. Optional: set `WANDB_API_KEY` as a Kaggle secret.

## Exporting to HF
```bash
python training/scripts/merge_lora.py \
  --base google/gemma-4-e4b-it \
  --adapter /kaggle/working/checkpoints/last \
  --out /kaggle/working/merged

python hf/publish_model.py \
  --path /kaggle/working/merged \
  --repo "$HF_ORG/$HF_MODEL_REPO"
```

Requires `HF_HUB_TOKEN` as a Kaggle secret.
