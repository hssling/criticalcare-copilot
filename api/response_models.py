"""Pydantic response models mirroring data/schemas/response_schema.json."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Alert(BaseModel):
    type: str
    severity: Literal["low", "medium", "high", "critical"]
    source: Literal["rule", "model", "retrieval"]
    message: str
    rationale: str | None = None
    rule_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    title: str
    snippet: str
    source_id: str


class CopilotResponse(BaseModel):
    summary: str = ""
    active_problems: list[str] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    uncertainty: Literal["low", "medium", "high"] = "high"
    escalation: str = ""
    review_required: bool = True
    evidence: list[Evidence] = Field(default_factory=list)
    model_version: str | None = None
    abstained: bool = False
