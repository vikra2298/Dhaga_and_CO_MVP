"""Overview agent. After Review, turns counted metrics into a weekly brief for Neha.

Code owns every number. The model only writes plain-language bullets from those facts.
If keys are missing, a deterministic template still runs so the dashboard never invents data.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

PROMPT = """You are Overview, an internal briefing agent for Neha (Category Head) at Dhaga & Co.
Write a weekly return-intelligence overview from the FACTS JSON only.
Return JSON only:
{"headline":"<one sentence>","bullets":["<short bullet>","..."],"watch":["<SKU — why>","..."],"actions":["<what Neha should do this week>","..."],"caveat":"<one sentence about limits>"}
Rules:
- Use only numbers and names present in FACTS. Do not invent rupees, return-rate drops, or trends vs prior weeks.
- Prefer fit / SKU / vendor clusters and open review rows.
- Keep bullets short. Max 5 bullets, max 3 watch items, max 3 actions.
- Say this is one file snapshot treated as the week's Other returns for the MVP.
- If FACTS say leave_alone rows need no catalogue action, say so.
"""


class OverviewDraft(BaseModel):
    headline: str = Field(min_length=8, max_length=280)
    bullets: list[str] = Field(min_length=1, max_length=5)
    watch: list[str] = Field(default_factory=list, max_length=3)
    actions: list[str] = Field(default_factory=list, max_length=3)
    caveat: str = Field(min_length=8, max_length=320)


@dataclass
class OverviewResult:
    ok: bool
    headline: str
    bullets: list[str] = field(default_factory=list)
    watch: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    caveat: str = ""
    source: str = "template"
    detail: str = ""
    error: str | None = None


def facts_from_insights(total: int, accepted: int, in_review: int, insights: dict, auto_approved: int) -> dict:
    """Pack only what Overview is allowed to narrate."""
    focus = insights.get("focus")
    return {
        "period": "this_week_file_snapshot",
        "total_other_comments": total,
        "counted": accepted,
        "counted_pct": insights.get("counted_pct", 0),
        "still_with_neha": in_review,
        "auto_approved": auto_approved,
        "leave_alone": insights.get("leave_alone", 0),
        "leave_pct": insights.get("leave_pct", 0),
        "areas": [
            {"title": a["title"], "count": a["count"], "share_pct": a["share_pct"], "actionable": a["actionable"]}
            for a in insights.get("areas", [])
            if a.get("count")
        ],
        "top_skus": [
            {"sku": p["sku"], "vendor": p["vendor"], "count": p["count"], "top_title": p["top_title"]}
            for p in insights.get("products", [])[:4]
        ],
        "focus": focus,
        "open_examples": [
            {"sku": a["sku"], "size": a["size"], "text": a["text"], "why": a["why"]}
            for a in insights.get("attention", [])[:3]
        ],
        "limits": insights.get("limit", ""),
    }


def template_overview(facts: dict) -> OverviewResult:
    """Deterministic brief. Always available; never invents metrics."""
    total = facts["total_other_comments"]
    counted = facts["counted"]
    open_n = facts["still_with_neha"]
    areas = facts.get("areas") or []
    top_area = areas[0] if areas else None
    focus = facts.get("focus")
    bullets: list[str] = [
        f"{counted} of {total} Other comments are counted ({facts.get('counted_pct', 0)}%). "
        f"{facts.get('auto_approved', 0)} filed without a click.",
    ]
    if top_area:
        bullets.append(
            f"Largest bucket: {top_area['title']} — {top_area['count']} rows ({top_area['share_pct']}%)."
        )
    if facts.get("leave_pct"):
        bullets.append(
            f"{facts['leave_pct']}% of counted rows need no catalogue change (vague dislike or not a product issue)."
        )
    if open_n:
        bullets.append(f"{open_n} still open for Neha (under 75% or no score).")
    watch: list[str] = []
    for item in facts.get("top_skus") or []:
        watch.append(f"{item['sku']} ({item['vendor']}) — {item['count']} counted, mostly {item['top_title']}")
        if len(watch) >= 3:
            break
    actions: list[str] = []
    if open_n:
        actions.append(f"Clear the review queue ({open_n} open).")
    if focus:
        actions.append(
            f"Check {focus['sku']} size {focus['size']} at {focus['vendor']}: {focus['action']}"
        )
    if not actions:
        actions.append("No open review rows. Scan top SKUs if a vendor size chart looks wrong.")
    headline = (
        f"Weekly overview · {counted} labeled Other returns this file, "
        f"{open_n} still with Neha."
        if total
        else "Weekly overview · upload a file to brief the week."
    )
    return OverviewResult(
        ok=True,
        headline=headline,
        bullets=bullets[:5],
        watch=watch[:3],
        actions=actions[:3],
        caveat=(
            "One file snapshot treated as this week’s Other returns. "
            "Does not remeasure the brief’s 31% return rate or 44% Other share."
        ),
        source="template",
        detail="Built from counted labels only. No model call.",
    )


async def _narrate(facts: dict) -> OverviewDraft:
    key = os.environ["MODEL_B_API_KEY"]
    name = os.environ["MODEL_B_NAME"]
    base = os.getenv("MODEL_B_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": name,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"FACTS:\n{json.dumps(facts, ensure_ascii=False)}"},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
        if response.status_code == 400 and "response_format" in payload:
            payload.pop("response_format")
            response = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return OverviewDraft.model_validate(json.loads(raw))


def _models_ready() -> bool:
    return bool(os.getenv("MODEL_B_API_KEY") and os.getenv("MODEL_B_NAME"))


async def write_weekly_overview(
    total: int,
    accepted: int,
    in_review: int,
    insights: dict,
    auto_approved: int,
) -> OverviewResult:
    """Run after Review. Prefer Model B narrative; fall back to the template."""
    facts = facts_from_insights(total, accepted, in_review, insights, auto_approved)
    fallback = template_overview(facts)
    if not _models_ready():
        fallback.detail = "Model B key missing. Showing the template brief from counted labels."
        return fallback
    try:
        draft = await _narrate(facts)
    except (httpx.HTTPError, json.JSONDecodeError, ValidationError, KeyError, TypeError) as exc:
        fallback.source = "template"
        fallback.detail = f"Overview model failed; template used. {exc}"
        fallback.error = str(exc)
        return fallback
    return OverviewResult(
        ok=True,
        headline=draft.headline.strip(),
        bullets=[b.strip() for b in draft.bullets if b.strip()][:5],
        watch=[w.strip() for w in draft.watch if w.strip()][:3],
        actions=[a.strip() for a in draft.actions if a.strip()][:3],
        caveat=draft.caveat.strip(),
        source="model",
        detail="Model B wrote the brief from code-owned facts.",
    )


def overview_public(result: OverviewResult | None) -> dict:
    if result is None:
        empty = template_overview(
            {
                "total_other_comments": 0,
                "counted": 0,
                "counted_pct": 0,
                "still_with_neha": 0,
                "auto_approved": 0,
                "leave_alone": 0,
                "leave_pct": 0,
                "areas": [],
                "top_skus": [],
                "focus": None,
                "open_examples": [],
                "limits": "",
            }
        )
        result = empty
    return {
        "name": "Overview",
        "headline": result.headline,
        "bullets": result.bullets,
        "watch": result.watch,
        "actions": result.actions,
        "caveat": result.caveat,
        "source": result.source,
        "detail": result.detail,
    }


__all__ = [
    "OverviewResult",
    "facts_from_insights",
    "overview_public",
    "template_overview",
    "write_weekly_overview",
]
