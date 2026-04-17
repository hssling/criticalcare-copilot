# Validation Plan

## Levels
1. **Unit** — schema, rule engine, data builders, response contract (`tests/`).
2. **Component** — prompt → model → schema round-trip on synthetic cases.
3. **Benchmark** — MedQA, MedMCQA, PubMedQA, ICU rubric, med-safety F1.
4. **External validation** — held-out eICU split never seen in training.
5. **Red-team** — adversarial suite (`eval/custom_sets/red_team.jsonl`).
6. **Human-in-the-loop** — clinician rubric ratings (rubrics in `eval/rubric_*.md`).

## Metrics
See [model-card-template.md](model-card-template.md). Primary safety metrics:
- `hallucinated_action_rate` (≤ baseline + 0 pp).
- `harmful_recommendation_rate` (≤ 0 in red-team).
- `abstention_correctness` (≥ baseline).
- `med_conflict_recall` (≥ baseline).

## Regression gate
`.github/workflows/eval.yml` runs a subset and compares to `eval/baseline_metrics.json`. CI fails if any of the safety metrics above regress.

## Cadence
- Unit + response contract: every PR.
- Lightweight eval: every PR.
- Full eval + external validation: nightly on `main` and on release candidates.
- Red-team: every release candidate; monthly on `main`.
- Human rubric: every release candidate (≥ 30 cases, ≥ 2 clinicians).

## Drift monitoring (post-deployment)
- Weekly rolling rule-firing-rate vs. baseline.
- Alert on distributional drift in case features (LOS, APACHE-II proxy, top diagnoses).
- Clinician feedback loop surfaced via audit log.
