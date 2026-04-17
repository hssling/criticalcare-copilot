"""Kaggle-aware runtime helpers.

Used by training scripts and notebooks to:
  * detect whether we are running on Kaggle / Colab / local,
  * auto-resolve dataset paths (Kaggle Input mounts, local fallbacks, synthetic),
  * pin checkpoint + artifact dirs to /kaggle/working when appropriate,
  * derive memory-aware defaults for Gemma 4 E4B QLoRA.

No heavy deps are imported at module load time, so this is safe to import
in CI without torch installed.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

KAGGLE_INPUT = Path("/kaggle/input")
KAGGLE_WORKING = Path("/kaggle/working")
COLAB_MARKER = Path("/content")


def on_kaggle() -> bool:
    return KAGGLE_INPUT.exists() and KAGGLE_WORKING.exists()


def on_colab() -> bool:
    return COLAB_MARKER.exists() and not on_kaggle()


def runtime_name() -> str:
    if on_kaggle():
        return "kaggle"
    if on_colab():
        return "colab"
    return "local"


# ---------------------------------------------------------------------------
# Dataset autodetection
# ---------------------------------------------------------------------------

# Candidate Kaggle input dataset slugs we look for, in priority order.
# The first directory that exists wins; filenames inside are then matched
# by the fuzzy patterns below.
_KAGGLE_DATASET_HINTS: dict[str, list[str]] = {
    "train": [
        "criticalcare-processed/train.jsonl",
        "criticalcare-copilot/train.jsonl",
        "train.jsonl",
    ],
    "valid": [
        "criticalcare-processed/valid.jsonl",
        "criticalcare-copilot/valid.jsonl",
        "valid.jsonl",
    ],
    "test": [
        "criticalcare-processed/test.jsonl",
        "criticalcare-copilot/test.jsonl",
        "test.jsonl",
    ],
    "safety_pairs": [
        "criticalcare-processed/safety_pairs.jsonl",
        "safety_pairs.jsonl",
    ],
}


def _find_in_kaggle_inputs(relative: str) -> Path | None:
    if not on_kaggle():
        return None
    # Direct hit at /kaggle/input/<anything>/<relative>
    for ds_dir in sorted(KAGGLE_INPUT.iterdir()) if KAGGLE_INPUT.exists() else []:
        cand = ds_dir / relative
        if cand.exists():
            return cand
        # Also try the bare filename under any depth (shallow search).
        for p in ds_dir.rglob(Path(relative).name):
            if p.is_file():
                return p
    return None


def resolve_dataset_path(split: str, repo_root: Path | None = None) -> Path:
    """Return the best-available path for a dataset split.

    Resolution order:
      1. Explicit env override:  CCC_<SPLIT>_PATH   (e.g. CCC_TRAIN_PATH)
      2. Kaggle input mounts (if on Kaggle)
      3. Local processed dir:    <repo>/data/processed/<split>.jsonl
      4. Synthetic fallback:     <repo>/data/sample/<split>.jsonl
    """
    env_key = f"CCC_{split.upper()}_PATH"
    if os.getenv(env_key):
        return Path(os.environ[env_key])

    if on_kaggle():
        for hint in _KAGGLE_DATASET_HINTS.get(split, []):
            p = _find_in_kaggle_inputs(hint)
            if p is not None:
                return p

    root = repo_root or _infer_repo_root()
    processed = root / "data" / "processed" / f"{split}.jsonl"
    if processed.exists():
        return processed

    sample = root / "data" / "sample" / f"{split}.jsonl"
    return sample


def _infer_repo_root() -> Path:
    # training/kaggle_runtime.py -> repo root is parents[1]
    return Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Output / checkpoint dirs
# ---------------------------------------------------------------------------

def resolve_output_dir(config_output: str | None, job: str = "run") -> Path:
    """Pick a writable output dir, preferring /kaggle/working on Kaggle.

    `config_output` is the value from the YAML config (e.g. "checkpoints/gemma4_e4b_qlora").
    If we're on Kaggle, we always redirect to /kaggle/working/<basename>.
    """
    if on_kaggle():
        name = Path(config_output or job).name or job
        out = KAGGLE_WORKING / name
    elif config_output:
        out = Path(config_output)
    else:
        out = _infer_repo_root() / "checkpoints" / job
    out.mkdir(parents=True, exist_ok=True)
    return out


def artifacts_dir() -> Path:
    root = KAGGLE_WORKING if on_kaggle() else _infer_repo_root() / "artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def find_latest_checkpoint(output_dir: Path) -> Path | None:
    """Trainer writes `checkpoint-<step>/` subdirs. Return the highest-step one."""
    if not output_dir.exists():
        return None
    ckpts = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("checkpoint-")]
    if not ckpts:
        return None
    ckpts.sort(key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else -1)
    return ckpts[-1]


# ---------------------------------------------------------------------------
# Memory-aware defaults
# ---------------------------------------------------------------------------

@dataclass
class MemoryProfile:
    gpu_name: str = "unknown"
    gpu_gb: float = 0.0
    num_gpus: int = 0
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    max_seq_len: int = 2048
    use_4bit: bool = True
    gradient_checkpointing: bool = True
    optim: str = "paged_adamw_8bit"
    bf16: bool = True
    fp16: bool = False
    attn_impl: str = "sdpa"
    extra: dict[str, Any] = field(default_factory=dict)


def detect_memory_profile() -> MemoryProfile:
    """Introspect GPU and return a MemoryProfile tuned for Gemma 4 E4B QLoRA.

    Works without torch installed (returns a safe CPU profile).
    """
    prof = MemoryProfile()
    try:
        import torch
    except Exception:
        prof.optim = "adamw_torch"
        prof.use_4bit = False
        prof.bf16 = False
        prof.extra["note"] = "torch unavailable; CPU profile"
        return prof

    if not torch.cuda.is_available():
        prof.optim = "adamw_torch"
        prof.use_4bit = False
        prof.bf16 = False
        prof.extra["note"] = "no CUDA; CPU profile"
        return prof

    prof.num_gpus = torch.cuda.device_count()
    props = torch.cuda.get_device_properties(0)
    prof.gpu_name = props.name
    prof.gpu_gb = round(props.total_memory / (1024 ** 3), 1)

    # bf16 support: Ampere+ (compute capability >= 8.0).
    cc = torch.cuda.get_device_capability(0)
    prof.bf16 = cc[0] >= 8
    prof.fp16 = not prof.bf16
    # Flash/SDP selection: transformers picks sdpa by default; keep it.
    prof.attn_impl = "sdpa"

    # Tier the schedule on total VRAM (Kaggle P100=16GB, T4=15GB, T4x2=2x15, L4=24, A100-40/80).
    g = prof.gpu_gb
    if g >= 70:
        prof.per_device_train_batch_size = 4
        prof.gradient_accumulation_steps = 4
        prof.max_seq_len = 4096
    elif g >= 38:
        prof.per_device_train_batch_size = 2
        prof.gradient_accumulation_steps = 8
        prof.max_seq_len = 3072
    elif g >= 22:
        prof.per_device_train_batch_size = 1
        prof.gradient_accumulation_steps = 16
        prof.max_seq_len = 2048
    else:  # 15–16 GB (T4 / P100)
        prof.per_device_train_batch_size = 1
        prof.gradient_accumulation_steps = 32
        prof.max_seq_len = 1536

    if prof.num_gpus > 1:
        # Effective batch size already grows with ddp; trim accumulation.
        prof.gradient_accumulation_steps = max(2, prof.gradient_accumulation_steps // prof.num_gpus)

    return prof


def apply_memory_profile(cfg: dict[str, Any], prof: MemoryProfile | None = None) -> dict[str, Any]:
    """Mutate a loaded training YAML in-place with memory-aware overrides.

    Honors CCC_FORCE_CONFIG=1 to skip all overrides.
    """
    if os.getenv("CCC_FORCE_CONFIG") == "1":
        return cfg
    prof = prof or detect_memory_profile()

    cfg.setdefault("training", {})
    t = cfg["training"]
    t["per_device_train_batch_size"] = prof.per_device_train_batch_size
    t["per_device_eval_batch_size"] = 1
    t["gradient_accumulation_steps"] = prof.gradient_accumulation_steps
    t["gradient_checkpointing"] = prof.gradient_checkpointing
    t["optim"] = prof.optim
    t["bf16"] = prof.bf16
    t["fp16"] = prof.fp16

    cfg.setdefault("data", {})
    cfg["data"]["max_seq_len"] = min(cfg["data"].get("max_seq_len", 2048), prof.max_seq_len)

    cfg.setdefault("model", {}).setdefault("quantization", {})
    cfg["model"]["quantization"]["enabled"] = prof.use_4bit
    cfg["model"]["attn_implementation"] = prof.attn_impl
    return cfg


# ---------------------------------------------------------------------------
# Artifact packaging
# ---------------------------------------------------------------------------

def package_artifact(src: Path, name: str | None = None) -> Path:
    """Zip a directory into artifacts_dir()/<name>.zip and return the archive path.

    On Kaggle this lands in /kaggle/working so it's downloadable from the
    notebook's Output pane.
    """
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(src)
    name = name or src.name
    base = artifacts_dir() / name
    archive = shutil.make_archive(str(base), "zip", root_dir=str(src))
    return Path(archive)


def write_run_metadata(output_dir: Path, extra: dict[str, Any] | None = None) -> Path:
    """Persist a small JSON describing the run so downstream notebooks can pick it up."""
    meta = {
        "runtime": runtime_name(),
        "output_dir": str(output_dir),
        "memory_profile": detect_memory_profile().__dict__,
    }
    if extra:
        meta.update(extra)
    path = output_dir / "run_metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return path
