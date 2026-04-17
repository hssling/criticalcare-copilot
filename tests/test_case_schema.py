from safety.schema_validation import validate_case


def _minimal_case(**overrides):
    c = {
        "case_id": "t-1",
        "demographics": {"age_years": 60, "sex": "M"},
        "encounter": {"encounter_id": "e", "admission_ts": "2026-04-17T10:00:00Z"},
        "icu_stay": {"stay_id": "s", "icu_admit_ts": "2026-04-17T11:00:00Z"},
        "provenance": {"source": "test", "extracted_ts": "2026-04-17T12:00:00Z"},
        "review_required": True,
    }
    c.update(overrides)
    return c


def test_minimal_case_is_valid():
    assert validate_case(_minimal_case()) == []


def test_bad_age_fails():
    errs = validate_case(_minimal_case(demographics={"age_years": -1, "sex": "M"}))
    assert any("age_years" in e for e in errs)


def test_missing_icu_stay_fails():
    c = _minimal_case()
    c.pop("icu_stay")
    errs = validate_case(c)
    assert any("icu_stay" in e for e in errs)


def test_unknown_sex_allowed_as_string():
    errs = validate_case(_minimal_case(demographics={"age_years": 40, "sex": "unknown"}))
    assert errs == []
