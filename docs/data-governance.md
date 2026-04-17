# Data Governance

## Principles
- **Least data**: only ingest what a task requires.
- **No redistribution**: restricted datasets (MIMIC-IV, eICU, n2c2) must be user-provided; this repo never ships them.
- **PHI awareness**: assume any real clinical record is PHI. De-identify on ingestion or work inside a governance-approved environment.
- **Provenance**: every case carries `provenance` metadata (source, version, extraction timestamp).
- **Consent boundaries**: never mix datasets across consent scopes; respect DUA terms.

## Data sources
| Source | License / DUA | Where it lives |
|--------|---------------|----------------|
| MIMIC-IV | PhysioNet credentialed | `$MIMIC_IV_ROOT` (user-mounted) |
| MIMIC-IV-Note | PhysioNet credentialed | `$MIMIC_IV_NOTE_ROOT` |
| eICU-CRD | PhysioNet credentialed | `$EICU_ROOT` |
| n2c2 ADE | n2c2 DUA | `$N2C2_ADE_ROOT` |
| Local protocols / guidelines | Institutional | `rag/sources/` (never committed unless public) |

## De-identification expectations
- Inputs must be HIPAA Safe Harbor de-identified (or equivalent jurisdictional standard) before fine-tuning.
- Free-text notes must be scrubbed for names, MRNs, dates outside PhysioNet offsets, and free-form contact info.
- Builders validate dates are within expected offset windows.

## Storage
- `data/raw/` — user-mounted, `.gitignore`d.
- `data/interim/` — intermediate JSONL, `.gitignore`d.
- `data/processed/` — finalized train/val/test JSONL + RAG index, `.gitignore`d.
- Artifacts that are safe to publish (synthetic samples, benchmark summaries) live in `docs/` or are explicitly allow-listed.

## Audit trail
Every inference call produces an audit record:
- `ts`, `user_id`, `case_hash`, `model_version`, `rule_pack_versions`, `rules_fired`, `review_required`, `schema_valid`, `latency_ms`.
See `app/functions/audit_log.ts` and `safety/rule_engine.py`.

## Retention
- Audit logs: 7 years (or jurisdictional requirement, whichever is longer).
- Model outputs: hashed + linked to case hash; raw outputs retained for QA review.
- Training data: per DUA; never longer than the DUA allows.
