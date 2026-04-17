# Production Release Checklist

Before tagging and deploying a new version of the criticalcare-copilot, ensure the following steps are completed.

## 1. Security & Compliance
- [x] **PHI Redaction Verified**: Redaction hooks implemented in both Python and TypeScript stacks.
- [x] **Audit Logging Enabled**: Event schemas created and redaction active.
- [ ] **Data Residency**: Verify that the HF inference endpoint is hosted in a region compliant.

## 2. Model & Fallback Testing
- [x] **Smoke Test**: Integrated into GitHub Actions `eval.yml` and Kaggle Master Pipeline.
- [ ] **Full Eval**: Execute manually before major releases.
- [x] **Fallback Validation**: Safe error responses and Rule Engine fail-soft active.

## 3. Resilience & Limits
- [x] **Rate Limiting Configured**: Scaffolding added to Python API and TS logic.
- [x] **Inference Timeout Check**: Set to 45s-60s with jittered retries.
- [x] **Input Sanitization**: 256KB hard limits enforced in headers.

## 4. Frontend & User Experience
- [x] **Safe Error Rendering**: Frontend updated to show Reference IDs + safe messages.
- [ ] **Guardrail Enforcement**: Verify final model card behavior.

## 5. Deployment
- [x] **Feature Flags Reviewed**: Environment variables gated.
- [x] **Environment Secrets Synced**: GitHub and Netlify secrets injected.
- [x] **CI Pipeline Passed**: Continuous validation for build, eval, and model documentation.
