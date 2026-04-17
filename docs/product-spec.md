# Product Specification

## Vision
An ICU-focused AI copilot that helps clinicians understand complex cases, surface medical errors early, and apply institutional protocols consistently — while remaining strictly **review-required** and never autonomous.

## Users
- ICU attendings, fellows, residents, bedside intensivists.
- Critical care nurses (read-only alert viewer).
- Clinical pharmacists (medication safety view).
- Quality/safety officers (audit view).

## Scope (in)
1. **Case understanding** — summarization, active problem list, trend interpretation, red flags, handoff notes, differential support, missing-data identification.
2. **Management assistance** — protocol-grounded checklists, monitoring suggestions, escalation triggers, "what to review next" hints.
3. **Medical error alerting** — duplicate therapy, renal/hepatic dose risk, contraindications, allergy conflicts, missed monitoring, ADE suspicion, bundle/prophylaxis omissions, handoff inconsistency.
4. **RAG grounding** — local protocols, guidelines, monographs with traceable citations.
5. **Audit + safety** — request/response logging, model version logging, rule firings, review flags.

## Scope (out)
- Autonomous order entry.
- Dosing calculators as binding recommendations.
- Standalone diagnostic authority.
- Use in pediatric, neonatal, or out-of-ICU settings without separate validation.
- Direct CPOE integration in v1.

## Product surfaces
- **Dashboard** — case queue, unread alerts, system health.
- **New case** — paste or upload structured case JSON.
- **Case summary** — timeline, active problems, rationale drawer.
- **Medication safety** — dedicated alert list with severity ranking.
- **Alert console** — cross-case view for pharmacists/safety officers.
- **Audit viewer** — who asked what, which model version, which rules fired.
- **Settings** — model version, endpoint health.

## Success metrics (clinical pilot)
- ≥0.80 red-flag recall vs. expert rubric.
- ≥0.85 medication-conflict recall; FP rate capped for deployability.
- Zero harmful autonomous recommendations in red-team set.
- Median response latency < 4s for E4B endpoint.
- Clinician rating ≥ 4/5 for "useful for handoff."

## Non-goals
- Marketing it as an AI doctor.
- Replacing institutional order sets.
- Training on identifiable PHI without IRB / governance approval.
