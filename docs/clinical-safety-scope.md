# Clinical Safety Scope

This document defines the **intended use**, **out-of-scope use**, and **safety architecture** of criticalcare-copilot. It binds every other component of the system.

## Intended use
- **Who**: licensed critical-care clinicians operating in an ICU with existing institutional safety processes.
- **What**: AI-assisted case understanding, protocol-grounded suggestions, and medical-error alerting.
- **How**: clinician enters structured case data; the system returns a structured JSON response (`review_required: true` by default) combining deterministic rule firings, model-generated rationale, and retrieved evidence snippets. The clinician remains the decision-maker.

## Out-of-scope use (prohibited)
- Autonomous order entry, prescribing, or dose calculation without human review.
- Non-ICU settings (pediatric, neonatal, outpatient, ED) without separate validation.
- Direct patient-facing chat.
- Training or inference on identifiable PHI outside of governance-approved environments.
- Use without audit logging enabled.

## Safety architecture (defense in depth)

```
1. Input schema validation
2. Deterministic rule engine  ──► may independently raise alerts
3. Prompt template with safety + abstention constraints
4. Model inference (fine-tuned Gemma 4, temperature bounded)
5. Output guardrails (schema validation, banned-phrase filter, severity check)
6. Merge step — rules + model + RAG citations
7. review_required defaults to true; escalation strings injected when appropriate
8. Audit logging (every step, every version)
```

## Core invariants enforced in code
1. Every response MUST conform to `data/schemas/response_schema.json`.
2. `review_required` MUST be `true` unless the output is a pure informational snippet AND all guardrails pass.
3. Responses MUST NOT contain autonomous imperative orders (e.g., "Give 2g vancomycin IV now"). Phrasing MUST be advisory ("Consider reviewing…", "Escalate if…").
4. If model output fails schema validation, the system falls back to rules-only output and logs a safety event.
5. Abstention is a valid and preferred response when data is insufficient or contradictory.

## Abstention triggers
- Missing essential vitals or labs for the requested task.
- Conflicting data (e.g., two different weights, contradictory allergies).
- Out-of-scope request (pediatric, non-ICU).
- Model low confidence flag (self-reported `uncertainty == "high"`).

## High-risk categories
Medication dosing, vasoactive management, sedation titration, electrolyte replacement, transfusion, anticoagulation, antibiotic stewardship. All are treated with elevated caution: rule-engine alerts precede model output; phrasing is advisory; escalation string is populated.

## Red-team program
See [red-team-plan.md](red-team-plan.md). Run `eval/benchmark_runner.py --suite red_team` as part of release gating.

## Release gating
See [release-gating.md](release-gating.md). No production rollout without: passing baseline metrics, red-team sign-off, model card update, clinical lead approval.
