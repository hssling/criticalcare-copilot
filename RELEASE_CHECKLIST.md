# Production Release Checklist

Before tagging and deploying a new version of the criticalcare-copilot, ensure the following steps are completed.

## 1. Security & Compliance
- [ ] **PHI Redaction Verified**: Confirm that the redaction hooks in `api/redaction.py` catch newly added sensitive fields.
- [ ] **Audit Logging Enabled**: Ensure `AUDIT_LOG_PATH` is correctly configured and events are sinking properly to your SIEM.
- [ ] **Data Residency**: Verify that the HF inference endpoint is hosted in a region compliant with your data storage policies.

## 2. Model & Fallback Testing
- [ ] **Smoke Test**: Run the evaluation suite locally (`python -m eval.benchmark_runner --suite smoke`) and confirm no safety regressions.
- [ ] **Full Eval**: Run the full evaluation suite (`python -m eval.benchmark_runner --suite full`). Verify all QA and monitoring PRF metrics against `eval/baseline_metrics.json`.
- [ ] **Fallback Validation**: Test the API with `HF_ENDPOINT_URL` disabled to ensure the system gracefully degrades to rule-based safety checks without crashing.

## 3. Resilience & Limits
- [ ] **Rate Limiting Configured**: Confirm `RATE_LIMIT_RPM` and `RATE_LIMIT_BURST` are appropriate for the production environment cluster size.
- [ ] **Inference Timeout Check**: Ensure `HF_TIMEOUT_S` and `HF_MAX_RETRIES` are set correctly to avoid frontend timeouts while maintaining robust retry logic.
- [ ] **Input Sanitization**: Verify that `MAX_CASE_PAYLOAD_BYTES` is reasonably sized to prevent DoS via massive payloads.

## 4. Frontend & User Experience
- [ ] **Safe Error Rendering**: Trigger a predictable error (like sending bad validation JSON) and verify the frontend shows the safe error message + UUID instead of a raw stack trace.
- [ ] **Guardrail Enforcement**: Supply a prompt that tries to generate an autonomous order and verify it is rewritten to an advisory format.

## 5. Deployment
- [ ] **Feature Flags Reviewed**: Update `api/feature_flags.py` or the production environment block to set standard feature toggles (e.g., `FF_MODEL_V2`, `FF_RAG_ENABLED`).
- [ ] **Environment Secrets Synced**: Ensure HuggingFace token and Endpoint URL are securely injected via Netlify/K8s Secrets.
- [ ] **CI Pipeline Passed**: Ensure all GitHub Actions workflows (ci, eval, model-card-sync) passed on the `main` branch.
