"""Dhaga Return Intelligence API."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agents.intake import IngestError, load_and_batch
from backend.agents.route import classify_and_route
from backend.schemas.taxonomy import AUTO_APPROVE_AT, LABEL_TITLES
from backend.store import dashboard, decide, replace_with_run, review_queue, save_pipeline, seed_if_empty, sku_detail
from backend.workflows.classify import models_configured

@asynccontextmanager
async def lifespan(_app: FastAPI):
    seed_if_empty()
    yield


app = FastAPI(title="Dhaga Return Intelligence", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EditBody(BaseModel):
    label: str


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "models_configured": models_configured(), "auto_approve_pct": int(AUTO_APPROVE_AT * 100)}


@app.get("/api/dashboard")
def get_dashboard() -> dict:
    payload = dashboard()
    payload["models_configured"] = models_configured()
    payload["auto_approve_pct"] = int(AUTO_APPROVE_AT * 100)
    payload["label_options"] = [{"label": key, "title": title} for key, title in LABEL_TITLES.items()]
    return payload


@app.get("/api/sku/{sku}")
def get_sku(sku: str) -> dict:
    return sku_detail(sku)


@app.get("/api/review")
def get_review() -> dict:
    return {"rows": review_queue()}


@app.post("/api/review/{event_id}/approve")
def approve(event_id: str) -> dict:
    try:
        result = decide(event_id, "approve")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if result is None:
        raise HTTPException(404, "That review row is not open.")
    return {"ok": True}


@app.post("/api/review/{event_id}/dismiss")
def dismiss(event_id: str) -> dict:
    if decide(event_id, "dismiss") is None:
        raise HTTPException(404, "That review row is not open.")
    return {"ok": True}


@app.post("/api/review/{event_id}/edit")
def edit(event_id: str, body: EditBody) -> dict:
    try:
        result = decide(event_id, "edit", body.label)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if result is None:
        raise HTTPException(404, "That review row is not open.")
    return {"ok": True}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    payload = await file.read()
    try:
        intake = load_and_batch(payload)
    except IngestError as exc:
        raise HTTPException(400, exc.message) from exc

    intake_step = {
        "name": "Intake",
        "loaded": intake.loaded,
        "batches": len(intake.batches),
        "batch_size": intake.batch_size,
    }

    if not intake.rows:
        return {
            "classified": False,
            "message": "No Other comments were left to classify.",
            "kept": 0,
            "dropped": intake.dropped,
            "unclassified": [],
            "agents": {"intake": intake_step, "review": None},
        }

    if not models_configured():
        return {
            "classified": False,
            "message": "Intake loaded the comments. Review did not run because the model keys are missing. The dashboard was left unchanged.",
            "kept": intake.loaded,
            "dropped": intake.dropped,
            "unclassified": [
                {"return_id": row.return_id, "sku": row.sku, "text": row.other_text}
                for row in intake.rows[:30]
            ],
            "agents": {"intake": intake_step, "review": None},
        }

    routed = await classify_and_route(intake)
    replace_with_run(routed.records)
    save_pipeline(intake.loaded, len(intake.batches), routed.auto_approved, routed.sent_to_neha)
    threshold = int(AUTO_APPROVE_AT * 100)
    return {
        "classified": True,
        "message": (
            f"Intake batched {intake.loaded} comments. "
            f"Review filed {routed.auto_approved} at {threshold}% or above and sent {routed.sent_to_neha} to Neha."
        ),
        "kept": intake.loaded,
        "dropped": intake.dropped,
        "accepted": routed.auto_approved,
        "in_review": routed.sent_to_neha,
        "unclassified": [],
        "agents": {
            "intake": intake_step,
            "review": {
                "name": "Review",
                "auto_approved": routed.auto_approved,
                "sent_to_neha": routed.sent_to_neha,
                "threshold": threshold,
            },
        },
    }
