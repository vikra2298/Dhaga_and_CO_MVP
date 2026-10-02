"""Review agent. Runs after Intake. Auto-approves at 75% and sends the rest to Neha."""

import asyncio
from dataclasses import dataclass, field
from uuid import uuid4

from backend.agents.intake import IntakeResult
from backend.schemas.taxonomy import AUTO_APPROVE_AT
from backend.workflows.classify import ModelOutcome, classify_comment
from backend.workflows.ingest import RawReturn


@dataclass
class RouteResult:
    records: list[dict] = field(default_factory=list)
    auto_approved: int = 0
    sent_to_neha: int = 0


def _record(row: RawReturn, outcome: ModelOutcome) -> dict:
    auto = bool(outcome.ok and outcome.confidence is not None and outcome.confidence >= AUTO_APPROVE_AT)
    return {
        "id": uuid4().hex[:12],
        "return_id": row.return_id,
        "sku": row.sku,
        "category": row.category,
        "vendor": row.vendor,
        "size": row.size,
        "return_reason": row.return_reason,
        "other_text": row.other_text,
        "status": "accepted" if auto else "review",
        "label": outcome.label,
        "confidence": outcome.confidence if outcome.ok else None,
        "evidence_span": outcome.evidence_span if outcome.ok else None,
        "short_reason": outcome.short_reason or outcome.error or "",
        "final_label": outcome.label if auto else None,
        "auto_approved": 1 if auto else 0,
    }


async def classify_and_route(intake: IntakeResult) -> RouteResult:
    """Classify one batch at a time. File 75% and above. Leave the rest for Neha."""
    records: list[dict] = []
    for batch in intake.batches:
        outcomes = await asyncio.gather(*(classify_comment(row.other_text) for row in batch.rows))
        records.extend(_record(row, outcome) for row, outcome in zip(batch.rows, outcomes, strict=True))
    auto_approved = sum(1 for item in records if item["auto_approved"])
    return RouteResult(
        records=records,
        auto_approved=auto_approved,
        sent_to_neha=len(records) - auto_approved,
    )
