from api.service import CopilotService


class _StubClient:
    def generate(self, *, system_prompt, safety_prompt, case, task, evidence):
        return {
            "summary": "Stub summary.",
            "active_problems": ["Acute kidney injury"],
            "alerts": [],
            "recommendations": ["Consider reviewing nephrotoxic medications."],
            "missing_data": [],
            "uncertainty": "medium",
            "escalation": "",
            "evidence": [],
        }


def _case():
    return {
        "case_id": "api-1",
        "demographics": {"age_years": 68, "sex": "M", "weight_kg": 80},
        "encounter": {"encounter_id": "e", "admission_ts": "2026-04-17T10:00:00Z"},
        "icu_stay": {"stay_id": "s", "icu_admit_ts": "2026-04-17T11:00:00Z"},
        "medications": [{"name": "heparin", "start_ts": "2026-04-17T11:30:00Z", "status": "active", "class": "anticoagulant"}],
        "provenance": {"source": "test", "extracted_ts": "2026-04-17T12:00:00Z"},
        "review_required": True,
    }


def test_service_returns_schema_valid_response():
    svc = CopilotService(model_client=_StubClient())
    resp = svc.run(_case(), task="icu_summary", use_rag=False, use_model=True)
    assert resp["review_required"] is True
    assert resp["summary"]
    # heparin present => no VTE prophy omission alert
    assert not any(a.get("rule_id") == "prophy_vte_missing" for a in resp["alerts"])


def test_service_abstains_on_bad_input():
    svc = CopilotService(model_client=_StubClient())
    resp = svc.run({"case_id": "x"}, task="icu_summary")
    assert resp["abstained"] is True
    assert resp["uncertainty"] == "high"


def test_service_fires_penicillin_rule_without_model():
    svc = CopilotService(model_client=None)  # rules-only
    c = _case()
    c["allergies"] = [{"substance": "penicillin", "severity": "severe"}]
    c["medications"] = [{"name": "piperacillin-tazobactam", "start_ts": "2026-04-17T12:00:00Z", "status": "active"}]
    resp = svc.run(c, use_rag=False, use_model=False)
    assert any(a.get("rule_id") == "allergy_penicillin_vs_betalactam" for a in resp["alerts"])
