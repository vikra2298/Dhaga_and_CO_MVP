"""Structured model output. Invalid JSON never becomes a label."""

from pydantic import BaseModel, Field

from backend.schemas.taxonomy import Label


class Issue(BaseModel):
    label: Label
    confidence: float = Field(ge=0, le=1)
    evidence_span: str = Field(min_length=1)


class Classification(BaseModel):
    issues: list[Issue] = Field(min_length=1)
    needs_review: bool = False
    short_reason: str = ""
