"""CopilotService: orchestrates rules + optional model + optional RAG into a
schema-valid response. This is the Python analogue of the Netlify ``infer``
function and is exercised directly in tests and in the local FastAPI app.

Production hardening (v0.2):
  * Structured logging on every code path.
  * Audit events emitted for infer / abstain / guardrail-reject.
  * Input sanitised before processing.
  * Feature-flag gating for model version routing.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

from safety import (
    GuardrailError,
    RuleEngine,
    enforce_guardrails,
    validate_case,
    validate_response,
)
from rag.retriever import Retriever

from .audit import AuditAction, AuditEvent, AuditOutcome, emit_audit_event
from .feature_flags import Flag, flags
from .redaction import redact_case_for_logging
from .response_models import CopilotResponse
from .validation import sanitize_case

log = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).resolve().parents[1] / "training" / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


class CopilotService:
    def __init__(
        self,
        *,
        rule_engine: RuleEngine | None = None,
        retriever: Retriever | None = None,
        model_client=None,  # any object with .generate(prompt, *, case, task) -> dict
        model_version: str | None = None,
    ):
        self.rules = rule_engine or RuleEngine()
        self.retriever = retriever
        self.model_client = model_client
        self.model_version = model_version or os.getenv("HF_MODEL_REVISION", "dev")

    # ------------------------------------------------------------------
    def run(self, case: dict[str, Any], *, task: str = "icu_summary",
            use_rag: bool = True, use_model: bool = True) -> dict[str, Any]:
        request_id = uuid.uuid4().hex[:12]
        t0 = time.perf_counter()

        # 0. Sanitise input
        case = sanitize_case(case)

        log.info(
            "infer_start case_id=%s task=%s use_rag=%s use_model=%s",
            case.get("case_id", "-"), task, use_rag, use_model,
            extra={"data": {"request_id": request_id, "case_id": case.get("case_id")}},
        )

        # 1. Validate input case. Schema errors => abstain with explanation.
        errors = validate_case(case)
        if errors:
            log.warning(
                "input_validation_failed case_id=%s errors=%s",
                case.get("case_id", "-"), errors[:3],
                extra={"data": {"request_id": request_id}},
            )
            resp = self._abstain(
                reason="Input case failed schema validation.",
                missing=errors[:5],
            )
            self._emit_audit(
                AuditAction.VALIDATION_FAIL, AuditOutcome.REJECTED,
                request_id=request_id, case_id=case.get("case_id"),
                task=task, latency_ms=_ms(t0),
            )
            return resp

        # 2. Deterministic rules (always).
        hits = self.rules.evaluate(case)
        rule_alerts = [h.to_alert() for h in hits]

        # 3. Optional RAG (gated by feature flag).
        evidence: list[dict[str, Any]] = []
        rag_enabled = use_rag and flags.is_enabled(Flag.RAG_ENABLED)
        if rag_enabled and self.retriever is not None:
            query = self._rag_query(case, task)
            evidence = self.retriever.retrieve_evidence(query)

        # 4. Optional model (gated by feature flag).
        model_out: dict[str, Any] = {}
        if use_model and self.model_client is not None:
            try:
                model_out = self.model_client.generate(
                    system_prompt=_load_prompt("system_prompt.txt"),
                    safety_prompt=_load_prompt("safety_prompt.txt"),
                    case=case,
                    task=task,
                    evidence=evidence,
                )
                if not isinstance(model_out, dict):
                    model_out = {}
            except Exception as exc:
                # Degrade gracefully to rules-only.
                log.warning(
                    "model_call_failed case_id=%s exc=%s",
                    case.get("case_id", "-"), exc,
                    extra={"data": {"request_id": request_id}},
                )
                model_out = {}

        # 5. Merge rules + model + evidence into the response contract.
        merged = self._merge(case, rule_alerts, model_out, evidence)

        # 6. Guardrails + schema enforcement.
        try:
            enforce_guardrails(merged)
        except GuardrailError:
            log.error(
                "guardrail_reject case_id=%s", case.get("case_id", "-"),
                extra={"data": {"request_id": request_id}},
            )
            resp = self._abstain(reason="Output guardrails rejected the response.")
            self._emit_audit(
                AuditAction.GUARDRAIL_REJECT, AuditOutcome.REJECTED,
                request_id=request_id, case_id=case.get("case_id"),
                task=task, latency_ms=_ms(t0),
            )
            return resp

        errs = validate_response(merged)
        if errs:
            log.warning(
                "response_validation_failed case_id=%s errors=%s",
                case.get("case_id", "-"), errs[:3],
                extra={"data": {"request_id": request_id}},
            )
            resp = self._abstain(reason="Response failed schema validation.", missing=errs[:5])
            self._emit_audit(
                AuditAction.VALIDATION_FAIL, AuditOutcome.DEGRADED,
                request_id=request_id, case_id=case.get("case_id"),
                task=task, latency_ms=_ms(t0),
            )
            return resp

        merged["model_version"] = self.model_version
        latency = _ms(t0)

        log.info(
            "infer_ok case_id=%s task=%s rules_fired=%d latency_ms=%.1f",
            case.get("case_id", "-"), task, len(rule_alerts), latency,
            extra={"data": {"request_id": request_id}},
        )
        self._emit_audit(
            AuditAction.INFER, AuditOutcome.SUCCESS,
            request_id=request_id, case_id=case.get("case_id"),
            task=task, rules_fired=[h.rule_id for h in hits],
            latency_ms=latency,
        )

        return merged

    # ------------------------------------------------------------------
    def _merge(self, case: dict[str, Any], rule_alerts: list[dict[str, Any]],
               model_out: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        alerts = list(rule_alerts)
        for a in model_out.get("alerts", []) or []:
            if isinstance(a, dict) and a.get("type") and a.get("message"):
                a.setdefault("source", "model")
                a.setdefault("severity", "medium")
                a.setdefault("evidence_ids", [])
                alerts.append(a)

        out = {
            "summary": (model_out.get("summary") or "").strip(),
            "active_problems": list(model_out.get("active_problems", []) or []),
            "alerts": alerts,
            "recommendations": list(model_out.get("recommendations", []) or []),
            "missing_data": list(model_out.get("missing_data", []) or []),
            "uncertainty": model_out.get("uncertainty") or "high",
            "escalation": (model_out.get("escalation") or "").strip(),
            "review_required": True,
            "evidence": list(evidence) + list(model_out.get("evidence", []) or []),
            "abstained": bool(model_out.get("abstained", False)),
        }
        # Light fallback: if model produced no summary, name active problems from diagnoses.
        if not out["summary"]:
            dxs = [d.get("label", "") for d in case.get("diagnoses", []) if d.get("status") == "active"]
            if dxs:
                out["summary"] = "Active diagnoses: " + ", ".join(dxs[:5]) + "."
            else:
                out["summary"] = "Insufficient narrative data for a model-free summary; clinician review required."
        return out

    def _rag_query(self, case: dict[str, Any], task: str) -> str:
        dx = ", ".join(d.get("label", "") for d in case.get("diagnoses", [])[:5])
        meds = ", ".join(m.get("name", "") for m in case.get("medications", [])[:8])
        return f"{task}: diagnoses=[{dx}] medications=[{meds}]"

    def _abstain(self, *, reason: str, missing: list[str] | None = None) -> dict[str, Any]:
        resp = CopilotResponse(
            summary="Unable to produce a safe response.",
            missing_data=missing or [],
            uncertainty="high",
            escalation="Review input and escalate to the covering clinician.",
            abstained=True,
        ).model_dump()
        resp["alerts"] = [{
            "type": "other",
            "severity": "high",
            "source": "rule",
            "message": reason,
            "rationale": "Abstention is preferred over unsafe output.",
            "rule_id": "abstain.safety",
            "evidence_ids": [],
        }]
        enforce_guardrails(resp)
        return resp

    def _emit_audit(self, action: AuditAction, outcome: AuditOutcome, **kwargs: Any) -> None:
        try:
            emit_audit_event(AuditEvent(action=action, outcome=outcome, **kwargs))
        except Exception:
            log.debug("audit_emit_failed", exc_info=True)

    # Convenience ------------------------------------------------------
    def safety_only(self, case: dict[str, Any]) -> dict[str, Any]:
        return self.run(case, task="medication_safety", use_rag=False, use_model=False)

    # JSON convenience
    def to_json(self, obj: Any) -> str:
        return json.dumps(obj, indent=2, default=str)


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000
