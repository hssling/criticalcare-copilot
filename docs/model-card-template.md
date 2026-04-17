# Model Card — criticalcare-copilot (template)

> Auto-filled by `hf/generate_model_card.py` from `eval/reports/`.

## Model details
- **Name**: criticalcare-copilot-gemma4-e4b
- **Base**: google/gemma-4-e4b-it
- **Adapter**: QLoRA (4-bit NF4, r=16, alpha=32) — see `training/configs/gemma4_e4b_qlora.yaml`.
- **Version**: `{{model_version}}`
- **Commit**: `{{git_sha}}`
- **Release date**: `{{release_date}}`

## Intended use
Clinician-facing decision-support in ICU settings (adult, non-pregnant, critical care). **Review-required.** Every output must be verified by a licensed clinician.

## Out-of-scope use
- Autonomous order entry or prescribing.
- Pediatric / neonatal / outpatient / ED care without separate validation.
- Direct patient-facing use.
- Any use without audit logging.

## Training data
- De-identified ICU datasets (MIMIC-IV / eICU): user-provided.
- Medication safety: n2c2 ADE + synthetic near-miss pairs.
- Safety/abstention: curated preference pairs.

Dataset cards and builders live under `data/builders/`.

## Evaluation
See [validation-plan.md](validation-plan.md). Latest metrics (from `eval/reports/latest.json`):

| Metric | Value | Baseline | Δ |
|--------|-------|----------|---|
| ICU summary rubric | `{{icu_rubric}}` | `{{icu_rubric_baseline}}` | `{{Δ}}` |
| Red-flag recall | `{{red_flag_recall}}` | … | … |
| Med conflict recall | `{{med_conflict_recall}}` | … | … |
| Hallucinated action rate | `{{halluc_rate}}` | … | … |
| Abstention correctness | `{{abstention_acc}}` | … | … |
| MedQA | `{{medqa}}` | … | … |
| MedMCQA | `{{medmcqa}}` | … | … |
| PubMedQA | `{{pubmedqa}}` | … | … |

## Safety
- Output schema enforced (`data/schemas/response_schema.json`).
- Deterministic rule engine runs alongside model (`safety/rule_engine.py`).
- `review_required=true` by default.
- Red-team report: `eval/reports/red_team_{{version}}.md`.

## Known limitations
- May miss rare drug-drug interactions not covered in rule packs.
- Rationale quality degrades on notes with heavy abbreviation.
- External validation currently limited to eICU-derived split.

## Ethical considerations
- Do not deploy in populations under-represented in training data without separate validation.
- Monitor for performance drift; see [validation-plan.md](validation-plan.md).

## Citation
```
@software{criticalcare_copilot_2026,
  title  = {criticalcare-copilot},
  year   = {2026},
  url    = {https://github.com/<org>/criticalcare-copilot}
}
```
