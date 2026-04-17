# Custom eval sets

- `red_team.jsonl` — adversarial suite (autonomy violations, hallucinated doses, allergy misses, abstention failures, prompt injection).
- `abstention.jsonl` — cases where abstention is the correct response.
- `contradictions.jsonl` — cases with contradictory data points.
- `ood.jsonl` — out-of-ICU cases (pediatric, obstetric).

Each line conforms to the training-record shape: `{task, case, target[, unsafe_patterns, expected_abstain]}`.
