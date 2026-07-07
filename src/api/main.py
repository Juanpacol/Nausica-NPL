"""FastAPI serving layer.

    POST /auth/register        email+password -> JWT
    POST /auth/login           email+password -> JWT
    POST /analyze              text -> distortion probabilities + CFI (persisted)
    POST /reframe              text + session -> counselor reply + updated CFI
    GET  /trajectory/{id}      CFI evolution across a session's turns
    POST /predict_trajectory   distortion history -> predicted next-turn vector
    POST /rigidity_score       text -> embedding-axis rigidity score

Run:  uvicorn src.api.main:app --reload
All non-auth endpoints require a Bearer JWT. State lives in PostgreSQL
(src/db/) — sessions survive server restarts and belong to their user.
Models load lazily on first request.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as OrmSession

from src.auth.dependencies import get_current_user
from src.auth.routes import router as auth_router
from src.db.models import NoteAnalysis, Session, Turn, User
from src.db.session import get_db
from src.metrics.cognitive_flexibility_index import compute_cfi
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Nausica",
    description="Cognitive distortion analysis + Socratic reframing with CFI trajectory. "
    "Research prototype — not a medical device, outputs are not diagnoses.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "app://obsidian.md",  # Obsidian desktop plugin
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(auth_router)


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
    source: str = Field(default="api", pattern="^(api|obsidian|mobile)$")
    file_hash: str | None = Field(default=None, max_length=64)


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
def analyze(
    req: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    distortions = _classifier().predict(req.text)
    cfi = compute_cfi(distortions)

    # Persist derived scores only — never the raw text (local-first promise for
    # plugin/mobile sources; API analyses keep the same contract for consistency).
    if req.file_hash:
        existing = (
            db.query(NoteAnalysis)
            .filter_by(user_id=user.id, source=req.source, file_hash=req.file_hash)
            .first()
        )
        if existing:
            existing.distortions, existing.cfi = distortions, cfi
        else:
            db.add(NoteAnalysis(
                user_id=user.id, source=req.source, file_hash=req.file_hash,
                distortions=distortions, cfi=cfi,
            ))
    else:
        db.add(NoteAnalysis(
            user_id=user.id, source=req.source, distortions=distortions, cfi=cfi,
        ))
    db.commit()
    return AnalyzeResponse(distortions=distortions, cfi=cfi)


@app.post("/reframe", response_model=ReframeResponse)
def reframe(
    req: ReframeRequest,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    if req.session_id:
        session = db.get(Session, req.session_id)
        if session is None or session.user_id != user.id:
            raise HTTPException(status_code=404, detail="Unknown session_id")
    else:
        session = Session(user_id=user.id)
        db.add(session)
        db.flush()

    client_turns = [t for t in session.turns if t.role == "client"]
    prev_cfi = client_turns[-1].cfi if client_turns else None
    next_idx = len(session.turns)

    distortions = _classifier().predict(req.text)
    cfi = compute_cfi(distortions)

    # Phase 6 RAG: embed the client turn and retrieve this user's past exchanges
    # that measurably lowered CFI. Both steps degrade gracefully when the
    # rigidity embedder isn't trained yet.
    embedding = None
    exemplars = None
    try:
        from src.models.rag_retrieval import retrieve_effective_reframes

        embedding = _rigidity_embedder().model.encode([req.text])[0].tolist()
        exemplars = retrieve_effective_reframes(db, user.id, embedding) or None
    except FileNotFoundError:
        pass

    history = [{"role": t.role, "text": t.text} for t in session.turns]
    reply = _dialogue_backend().generate(distortions, req.text, history, exemplars)

    db.add(Turn(session_id=session.id, turn_idx=next_idx, role="client",
                text=req.text, distortions=distortions, cfi=cfi,
                embedding=embedding))
    db.add(Turn(session_id=session.id, turn_idx=next_idx + 1, role="counselor",
                text=reply))
    db.commit()

    return ReframeResponse(
        session_id=session.id,
        counselor_reply=reply,
        distortions=distortions,
        cfi=cfi,
        cfi_delta=(cfi - prev_cfi) if prev_cfi is not None else None,
    )


@app.get("/trajectory/{session_id}")
def trajectory(
    session_id: str,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    session = db.get(Session, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    client_turns = [t for t in session.turns if t.role == "client"]
    points = [
        {"turn": i + 1, "cfi": t.cfi, "distortions": t.distortions}
        for i, t in enumerate(client_turns)
    ]
    deltas = [b["cfi"] - a["cfi"] for a, b in zip(points, points[1:])]
    return {
        "session_id": session_id,
        "points": points,
        "delta": deltas[-1] if deltas else None,
        "is_improving": (sum(deltas) < 0) if deltas else None,
    }


# --------------------------------------------------- Phase 2: temporal dynamics


@lru_cache(maxsize=1)
def _temporal_model():
    from src.models.temporal_cfi import TemporalCFITransformer

    return TemporalCFITransformer.load()


class PredictTrajectoryRequest(BaseModel):
    history: list[dict[str, float]] = Field(min_length=1)


class PredictTrajectoryResponse(BaseModel):
    predicted_distortions: dict[str, float]
    predicted_cfi: float
    disclaimer: str = (
        "Research prototype output — not a clinical diagnosis. "
        "Temporal model trained on synthetic dialogue trajectories."
    )


@app.post("/predict_trajectory", response_model=PredictTrajectoryResponse)
def predict_trajectory(
    req: PredictTrajectoryRequest, user: User = Depends(get_current_user)
):
    try:
        model = _temporal_model()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Temporal model not trained yet — run: python -m src.models.temporal_cfi train",
        )
    pred = model.predict_next(req.history)
    return PredictTrajectoryResponse(
        predicted_distortions=pred, predicted_cfi=compute_cfi(pred)
    )


# ------------------------------------------------- Phase 2: rigidity embedding


@lru_cache(maxsize=1)
def _rigidity_embedder():
    from src.models.rigidity_embedding import RigidityEmbedder

    return RigidityEmbedder.load()


class RigidityScoreRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class RigidityScoreResponse(BaseModel):
    rigidity_score: float
    disclaimer: str = (
        "Research prototype output — not a clinical diagnosis. "
        "Embedding trained on synthetic (rigid, flexible) reformulation pairs."
    )


@app.post("/rigidity_score", response_model=RigidityScoreResponse)
def rigidity_score(
    req: RigidityScoreRequest, user: User = Depends(get_current_user)
):
    try:
        embedder = _rigidity_embedder()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Rigidity embedding not trained yet — "
            "run: python -m src.models.rigidity_embedding train",
        )
    return RigidityScoreResponse(rigidity_score=embedder.rigidity_score(req.text))


# ---------------------------------------------------- Phase 6: voice ingestion


@lru_cache(maxsize=1)
def _whisper():
    from faster_whisper import WhisperModel

    # base model: good enough for journaling audio; runs on CPU, fully local
    return WhisperModel("base", device="cpu", compute_type="int8")


@app.post("/analyze/audio", response_model=AnalyzeResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """Voice journaling: transcribe locally with faster-whisper, then run the
    exact same /analyze pipeline on the transcript. Audio never leaves the
    machine and is not stored — only the derived scores are."""
    try:
        model = _whisper()
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Audio support not installed — run: pip install -e '.[audio]'",
        )
    import tempfile
    from pathlib import Path as _Path

    suffix = _Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        segments, _info = model.transcribe(tmp.name)
        text = " ".join(s.text.strip() for s in segments).strip()

    if not text:
        raise HTTPException(status_code=422, detail="No speech detected in audio")
    return analyze(AnalyzeRequest(text=text, source="mobile"), user=user, db=db)


# ----------------------------------------------------- Phase 4: user profiling


@app.get("/profile/archetype")
def profile_archetype(
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """Dominant mindset archetype + trend over the user's full history
    (client turns from reframing sessions + one-shot note analyses)."""
    from src.models.archetypes import dominant_archetype

    turns = (
        db.query(Turn)
        .join(Session, Turn.session_id == Session.id)
        .filter(Session.user_id == user.id, Turn.role == "client")
        .order_by(Turn.created_at)
        .all()
    )
    notes = (
        db.query(NoteAnalysis)
        .filter_by(user_id=user.id)
        .order_by(NoteAnalysis.created_at)
        .all()
    )
    profiles = sorted(
        [(t.created_at, t.distortions) for t in turns if t.distortions]
        + [(n.created_at, n.distortions) for n in notes],
        key=lambda pair: pair[0],
    )
    result = dominant_archetype([p for _, p in profiles])
    result["n_texts"] = len(profiles)
    result["disclaimer"] = (
        "Research prototype output — not a clinical diagnosis. "
        "Archetypes are heuristic groupings of distortion signals."
    )
    return result


class CompositeRigidityRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


@app.post("/composite_rigidity")
def composite_rigidity(
    req: CompositeRigidityRequest,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """All three rigidity signals blended into one score (heuristic weights —
    see docs/VALIDATION.md). Temporal signal uses the user's recent history."""
    from src.metrics.composite_rigidity import compute_composite_rigidity

    distortions = _classifier().predict(req.text)
    cfi = compute_cfi(distortions)

    temporal_cfi = None
    try:
        recent = (
            db.query(Turn)
            .join(Session, Turn.session_id == Session.id)
            .filter(Session.user_id == user.id, Turn.role == "client")
            .order_by(Turn.created_at.desc())
            .limit(8)
            .all()
        )
        history = [t.distortions for t in reversed(recent) if t.distortions]
        history.append(distortions)
        temporal_cfi = compute_cfi(_temporal_model().predict_next(history))
    except FileNotFoundError:
        pass  # temporal model not trained — blend renormalizes without it

    embedding_rigidity = None
    try:
        embedding_rigidity = _rigidity_embedder().rigidity_score(req.text)
    except FileNotFoundError:
        pass

    result = compute_composite_rigidity(cfi, temporal_cfi, embedding_rigidity)
    result["distortions"] = distortions
    result["disclaimer"] = (
        "Research prototype output — not a clinical diagnosis. "
        "Composite weights are heuristic, not calibrated on real data."
    )
    return result


# ------------------------------------------------ Phase 4: clinical PDF report


def _collect_history(db: OrmSession, user_id: str) -> list[dict]:
    turns = (
        db.query(Turn)
        .join(Session, Turn.session_id == Session.id)
        .filter(Session.user_id == user_id, Turn.role == "client")
        .all()
    )
    notes = db.query(NoteAnalysis).filter_by(user_id=user_id).all()
    rows = [
        {"when": t.created_at, "cfi": t.cfi, "distortions": t.distortions}
        for t in turns if t.distortions is not None
    ] + [
        {"when": n.created_at, "cfi": n.cfi, "distortions": n.distortions}
        for n in notes
    ]
    return sorted(rows, key=lambda r: r["when"])


@app.get("/reports/{user_id}.pdf")
def clinical_report(
    user_id: str,
    requester: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """PDF progress report. Self-access always; clinicians need shared org +
    the patient's explicit consent (require_clinician_of)."""
    from datetime import datetime, timezone

    from fastapi.responses import Response

    from src.auth.dependencies import require_clinician_of
    from src.models.archetypes import dominant_archetype
    from src.reports.builder import build_report

    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Unknown user")
    require_clinician_of(db, requester, target)

    history = _collect_history(db, user_id)
    summary = dominant_archetype([r["distortions"] for r in history])
    summary["n_texts"] = len(history)
    pdf = build_report(target.email, history, summary, datetime.now(timezone.utc))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="nausica-report-{user_id}.pdf"'},
    )


# --------------------------------------------- Phase 7: clinician feedback loop


class TurnFeedbackRequest(BaseModel):
    good_reframe: bool
    correction_text: str | None = Field(default=None, max_length=4000)


@app.post("/turns/{turn_id}/feedback")
def turn_feedback(
    turn_id: str,
    req: TurnFeedbackRequest,
    requester: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """Clinician marks a counselor turn as a good/bad reframe (optionally with a
    corrected version). Feeds scripts/export_preference_pairs.py for future DPO."""
    from src.auth.dependencies import require_clinician_of

    turn = db.get(Turn, turn_id)
    if turn is None or turn.role != "counselor":
        raise HTTPException(status_code=404, detail="Unknown counselor turn")
    patient = db.get(User, db.get(Session, turn.session_id).user_id)
    require_clinician_of(db, requester, patient)

    turn.clinician_feedback_good = req.good_reframe
    turn.clinician_feedback_text = req.correction_text
    db.commit()
    return {"turn_id": turn_id, "recorded": True}


# ------------------------------------------------- Phase 5: consent management


class ConsentRequest(BaseModel):
    consent_clinician_view: bool


@app.get("/profile/consent")
def get_consent(user: User = Depends(get_current_user)):
    return {"consent_clinician_view": user.consent_clinician_view}


@app.post("/profile/consent")
def set_consent(
    req: ConsentRequest,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """Patient grants or revokes clinician visibility. Opt-in, reversible."""
    db_user = db.get(User, user.id)
    db_user.consent_clinician_view = req.consent_clinician_view
    db.commit()
    return {"consent_clinician_view": db_user.consent_clinician_view}


@app.get("/org/patients")
def org_patients(
    requester: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    """Clinician dashboard data: consenting patients in the requester's orgs with
    their dominant archetype + latest CFI. Patients without consent are invisible."""
    from src.db.models import OrgMembership
    from src.models.archetypes import dominant_archetype

    my_clinician_orgs = [
        m.org_id
        for m in db.query(OrgMembership).filter(
            OrgMembership.user_id == requester.id,
            OrgMembership.role.in_(["clinician", "admin"]),
        )
    ]
    if not my_clinician_orgs:
        raise HTTPException(status_code=403, detail="Not a clinician in any organization")

    patient_ids = {
        m.user_id
        for m in db.query(OrgMembership).filter(
            OrgMembership.org_id.in_(my_clinician_orgs),
            OrgMembership.role == "patient",
        )
    }
    out = []
    for pid in patient_ids:
        patient = db.get(User, pid)
        if not patient.consent_clinician_view:
            continue
        history = _collect_history(db, pid)
        summary = dominant_archetype([r["distortions"] for r in history])
        out.append({
            "user_id": pid,
            "email": patient.email,
            "n_texts": len(history),
            "latest_cfi": history[-1]["cfi"] if history else None,
            "archetype": summary["archetype"],
            "trend": summary["trend"],
        })
    return {"patients": sorted(out, key=lambda p: -(p["latest_cfi"] or 0))}


@app.get("/health")
def health():
    return {"status": "ok"}
