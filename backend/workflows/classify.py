"""Model A and Model B. Temperature 0. One JSON object per row."""

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

import httpx
from pydantic import ValidationError

from backend.schemas.outputs import Classification
from backend.schemas.taxonomy import AUTO_APPROVE_AT, LABELS

PROMPT = """You classify one Dhaga & Co. return comment written in Hinglish, Hindi, or English.
Return JSON only:
{{"issues":[{{"label":"<one label>","confidence":0.0,"evidence_span":"<exact substring of the comment>"}}],"needs_review":false,"short_reason":"<one sentence>"}}
Allowed labels: {labels}
Rules:
- evidence_span must be copied from the comment. Do not correct spelling.
- "acha nahi laga", "didn't like", and typos of that idea are insufficient_evidence when no fit, colour, or fabric fact is stated.
- A clear fit, colour, quality, size-chart, or delivery fact can be 75% or higher.
- If the comment does not support a product reason, use insufficient_evidence. Do not invent fit or fabric.
- confidence is 0 to 1.
- needs_review is true only when you are under 75% sure.
"""


@dataclass
class ModelOutcome:
    ok: bool
    label: str | None = None
    confidence: float | None = None
    evidence_span: str | None = None
    short_reason: str = ""
    error: str | None = None


def models_configured() -> bool:
    return bool(os.getenv("MODEL_A_API_KEY") and os.getenv("MODEL_A_NAME") and os.getenv("MODEL_B_API_KEY") and os.getenv("MODEL_B_NAME"))


def _quote_in_text(span: str, text: str) -> str | None:
    if span in text:
        return span
    folded = text.casefold()
    found = folded.find(span.casefold())
    if found == -1:
        return None
    return text[found : found + len(span)]


def _parse(raw: str, text: str) -> ModelOutcome:
    body = raw.strip()
    if body.startswith("```"):
        body = body.strip("`")
        body = body.removeprefix("json").strip()
    try:
        parsed = Classification.model_validate(json.loads(body))
    except (json.JSONDecodeError, ValidationError) as exc:
        return ModelOutcome(ok=False, error=f"Validation failed. {exc}")
    issue = max(parsed.issues, key=lambda item: item.confidence)
    quote = _quote_in_text(issue.evidence_span.strip(), text)
    if quote is None:
        return ModelOutcome(
            ok=False,
            error="Validation failed. The model quote was not in the customer’s text, so no score was stored.",
        )
    return ModelOutcome(
        ok=True,
        label=issue.label,
        confidence=issue.confidence,
        evidence_span=quote,
        short_reason=parsed.short_reason,
    )


async def _complete(which: str, text: str, prior: str | None) -> str:
    key = os.environ[f"MODEL_{which}_API_KEY"]
    name = os.environ[f"MODEL_{which}_NAME"]
    base = os.getenv(f"MODEL_{which}_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    system = PROMPT.format(labels=", ".join(LABELS))
    user = f"Comment:\n{text}"
    if prior:
        user += f"\n\nEarlier attempt to check:\n{prior}"
    payload = {
        "model": name,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
        if response.status_code == 400 and "response_format" in payload:
            payload.pop("response_format")
            response = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def classify_comment(text: str) -> ModelOutcome:
    """Cheap model, then the stronger model only when the row is under 75% or invalid."""
    if not models_configured():
        return ModelOutcome(
            ok=False,
            error="Model keys are missing. This row was not classified. Add MODEL_A and MODEL_B to .env.",
        )
    try:
        first = _parse(await _complete("A", text, None), text)
    except Exception as exc:  # noqa: BLE001 — show the failure, do not invent a label
        first = ModelOutcome(ok=False, error=f"Model A failed. {exc}")
    if first.ok and first.confidence is not None and first.confidence >= AUTO_APPROVE_AT:
        return first
    try:
        second = _parse(await _complete("B", text, first.short_reason or first.error), text)
    except Exception as exc:  # noqa: BLE001
        second = ModelOutcome(ok=False, error=f"Model B failed. {exc}")
    if second.ok:
        return second
    if first.ok:
        return first
    return second
