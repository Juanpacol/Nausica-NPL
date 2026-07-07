"""RAG retrieval for the Socratic dialogue (Phase 6).

Finds past (client turn, counselor reply) exchanges where the reply WORKED —
defined as the client's next turn in that session having a lower CFI — and whose
client turn is semantically similar to the current one. The top-k exchanges are
injected as few-shot exemplars into the reframing prompt.

Retrieval is scoped to the requesting user's own history: no cross-user leakage
of conversational patterns.

Cosine similarity runs in Python over JSON-stored embeddings — appropriate at
prototype scale (hundreds of turns). The scale-up path is pgvector (the
docker-compose db image already ships it); swap this module's query for a
`<->` ORDER BY when volume demands it.
"""

from __future__ import annotations

import math

from sqlalchemy.orm import Session as OrmSession

from src.db.models import Session, Turn
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm > 0 else 0.0


def retrieve_effective_reframes(
    db: OrmSession,
    user_id: str,
    query_embedding: list[float],
    k: int = 2,
    min_similarity: float = 0.35,
) -> list[dict]:
    """Top-k past exchanges of THIS user where the counselor reply lowered CFI.

    Returns [{"client_text", "counselor_text", "similarity", "cfi_drop"}, ...].
    """
    client_turns = (
        db.query(Turn)
        .join(Session, Turn.session_id == Session.id)
        .filter(
            Session.user_id == user_id,
            Turn.role == "client",
            Turn.embedding.isnot(None),
        )
        .all()
    )

    candidates = []
    for turn in client_turns:
        reply = (
            db.query(Turn)
            .filter_by(session_id=turn.session_id, turn_idx=turn.turn_idx + 1,
                       role="counselor")
            .first()
        )
        next_client = (
            db.query(Turn)
            .filter_by(session_id=turn.session_id, turn_idx=turn.turn_idx + 2,
                       role="client")
            .first()
        )
        if reply is None or next_client is None:
            continue
        if turn.cfi is None or next_client.cfi is None or next_client.cfi >= turn.cfi:
            continue  # only exchanges that actually reduced rigidity
        sim = cosine(query_embedding, turn.embedding)
        if sim < min_similarity:
            continue
        candidates.append({
            "client_text": turn.text,
            "counselor_text": reply.text,
            "similarity": sim,
            "cfi_drop": round(turn.cfi - next_client.cfi, 4),
        })

    candidates.sort(key=lambda c: -c["similarity"])
    return candidates[:k]
