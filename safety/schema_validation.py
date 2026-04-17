"""JSON-Schema validation for cases and responses.

The schemas live under ``data/schemas/`` and are loaded lazily. We use
``jsonschema`` with a local file resolver so ``$ref`` between schemas works
without network access.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, RefResolver

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "data" / "schemas"


@lru_cache(maxsize=8)
def _load(name: str) -> dict[str, Any]:
    with (SCHEMA_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load(schema_name)
    store: dict[str, Any] = {}
    for name in ("case_schema.json", "alert_schema.json", "response_schema.json"):
        s = _load(name)
        store[name] = s
        sid = s.get("$id")
        if sid:
            store[sid] = s
    resolver = RefResolver(
        base_uri=SCHEMA_DIR.as_uri() + "/",
        referrer=schema,
        store=store,
    )
    return Draft202012Validator(schema, resolver=resolver)


def validate_case(case: dict[str, Any]) -> list[str]:
    """Return a list of human-readable validation errors (empty == valid)."""
    v = _validator("case_schema.json")
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in v.iter_errors(case)]


def validate_response(resp: dict[str, Any]) -> list[str]:
    v = _validator("response_schema.json")
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in v.iter_errors(resp)]
