"""Pydantic request models. Kept permissive for the ``case`` payload so that
JSON-schema validation (authoritative) runs separately in the service.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class InferRequest(BaseModel):
    task: Literal[
        "icu_summary", "differential_support", "management_assistance",
        "medication_safety", "handoff_generation",
    ] = "icu_summary"
    case: dict[str, Any] = Field(..., description="Case object; validated against case_schema.json.")
    use_rag: bool = True
    use_model: bool = True


class SafetyCheckRequest(BaseModel):
    case: dict[str, Any]


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = 5
