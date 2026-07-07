"""FastAPI serving layer (Phase 6).

    POST /analyze              text -> distortion probabilities + CFI
    POST /reframe              text + session -> counselor's Socratic reply + updated CFI
    GET  /trajectory/{id}      CFI evolution across a session's turns

Run:  uvicorn src.api.main:app --reload
Models load lazily on first request (classifier checkpoint if present, else base
encoder with a warning). Sessions are in-memory — a research demo, not production.
"""

from __future__ import annotations

import uuid
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.metrics.cognitive_flexibility_index import ReframingTrajectory, compute_cfi
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Nausica",
    description="Cognitive distortion analysis + Socratic reframing with CFI trajectory. "
    "Research prototype — not a medical device, outputs are not diagnoses.",
    version="0.1.0",
)

# ------------------------------------------------------------------ state

_sessions: dict[str, dict] = {}  # session_id -> {"trajectory": ..., "history": [...]}


@lru_cache(maxsize=1)
def _classifier():
    from src.models.distortion_classifier import DistortionClassifier

    return DistortionClassifier.load()


@lru_cache(maxsize=1)
def _dialogue_backend():
    from src.models.reframing_dialogue import get_backend

    return get_backend()


# ------------------------------------------------------------------ schemas


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class AnalyzeResponse(BaseModel):
    distortions: dict[str, float]
    cfi: float
    disclaimer: str = "Research prototype output — not a clinical diagnosis."


class ReframeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None


class ReframeResponse(BaseModel):
    session_id: str
    counselor_reply: str
    distortions: dict[str, float]
    cfi: float
    cfi_delta: float | None
    disclaimer: str = "Research prototype output — not a clinical diagnosis."


# ------------------------------------------------------------------ endpoints


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    distortions = _classifier().predict(req.text)
    return AnalyzeResponse(distortions=distortions, cfi=compute_cfi(distortions))


@app.post("/reframe", response_model=ReframeResponse)
def reframe(req: ReframeRequest):
    session_id = req.session_id or str(uuid.uuid4())
    session = _sessions.setdefault(
        session_id, {"trajectory": ReframingTrajectory(session_id), "history": []}
    )

    distortions = _classifier().predict(req.text)
    point = session["trajectory"].add_turn(distortions)

    reply = _dialogue_backend().generate(distortions, req.text, session["history"])
    session["history"].append({"role": "client", "text": req.text})
    session["history"].append({"role": "counselor", "text": reply})

    return ReframeResponse(
        session_id=session_id,
        counselor_reply=reply,
        distortions=distortions,
        cfi=point.cfi,
        cfi_delta=session["trajectory"].delta,
    )


@app.get("/trajectory/{session_id}")
def trajectory(session_id: str):
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return session["trajectory"].to_dict()


@app.get("/health")
def health():
    return {"status": "ok"}
