from safety import enforce_guardrails, validate_response


def test_enforce_sets_review_required_and_rewrites_order():
    resp = {
        "summary": "Give 500 mg vancomycin IV now.",
        "active_problems": [],
        "alerts": [],
        "recommendations": ["Give 2 g ceftriaxone now."],
        "missing_data": [],
        "uncertainty": "low",
        "escalation": "",
        "review_required": False,
        "evidence": [],
    }
    enforce_guardrails(resp)
    assert resp["review_required"] is True
    assert "consider reviewing" in resp["summary"].lower()
    assert any("consider reviewing" in r.lower() for r in resp["recommendations"])


def test_response_schema_valid_shape():
    resp = {
        "summary": "ok",
        "active_problems": [],
        "alerts": [],
        "recommendations": [],
        "missing_data": [],
        "uncertainty": "low",
        "escalation": "",
        "review_required": True,
        "evidence": [],
    }
    assert validate_response(resp) == []


def test_response_schema_catches_bad_uncertainty():
    resp = {
        "summary": "ok", "active_problems": [], "alerts": [], "recommendations": [],
        "missing_data": [], "uncertainty": "crazy", "escalation": "",
        "review_required": True, "evidence": [],
    }
    assert validate_response(resp) != []
