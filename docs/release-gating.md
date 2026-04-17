# Release Gating

A release candidate may NOT be promoted to production unless **every** item below is satisfied.

## Automated gates (CI)
- [ ] `pytest` green.
- [ ] Lint green (Python + TS).
- [ ] Schema validation green on all synthetic samples and the dev set.
- [ ] Lightweight eval subset within tolerance of `eval/baseline_metrics.json`.
- [ ] Safety metrics (`hallucinated_action_rate`, `harmful_recommendation_rate`) ≤ baseline.
- [ ] Red-team `autonomy_violation_rate == 0`, `harmful_recommendation_rate == 0`.

## Manual gates
- [ ] Model card updated (`docs/model-card-template.md` → `eval/reports/<version>/model_card.md`).
- [ ] Clinical lead sign-off (name, date, version hash).
- [ ] Safety officer sign-off.
- [ ] Change log entry in `docs/validation-plan.md`.
- [ ] Data governance review if training data changed.

## Deployment gates
- [ ] Secrets rotated or verified in Netlify + HF.
- [ ] Audit log sink reachable.
- [ ] Rollback plan documented; previous deploy tagged.

## Post-deploy
- [ ] 24h smoke monitoring: rule-firing rate, error rate, latency.
- [ ] Clinician feedback channel live.
- [ ] Drift baseline captured.
