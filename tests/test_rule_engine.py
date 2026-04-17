from safety.rule_engine import RuleEngine


def _case(**kw):
    base = {
        "case_id": "t",
        "demographics": {"age_years": 65, "sex": "M", "weight_kg": 80},
        "encounter": {"encounter_id": "e", "admission_ts": "2026-04-17T10:00:00Z"},
        "icu_stay": {"stay_id": "s", "icu_admit_ts": "2026-04-17T11:00:00Z"},
        "provenance": {"source": "test", "extracted_ts": "2026-04-17T12:00:00Z"},
        "review_required": True,
    }
    base.update(kw)
    return base


def test_penicillin_allergy_fires():
    engine = RuleEngine()
    case = _case(
        allergies=[{"substance": "penicillin", "severity": "severe"}],
        medications=[{"name": "piperacillin-tazobactam", "start_ts": "2026-04-17T12:00:00Z", "status": "active"}],
    )
    hits = engine.evaluate(case)
    assert any(h.rule_id == "allergy_penicillin_vs_betalactam" for h in hits)


def test_hyperkalemia_fires():
    engine = RuleEngine()
    case = _case(labs=[{"ts": "2026-04-17T11:30:00Z", "name": "potassium", "value": 6.4}])
    hits = engine.evaluate(case)
    assert any(h.rule_id == "elyte_hyperkalemia" for h in hits)


def test_vte_prophy_missing_fires_when_no_anticoag():
    engine = RuleEngine()
    hits = engine.evaluate(_case(medications=[]))
    assert any(h.rule_id == "prophy_vte_missing" for h in hits)


def test_vte_prophy_not_fired_when_heparin_present():
    engine = RuleEngine()
    case = _case(medications=[{"name": "heparin", "start_ts": "2026-04-17T11:00:00Z", "status": "active"}])
    hits = engine.evaluate(case)
    assert not any(h.rule_id == "prophy_vte_missing" for h in hits)
