"""RAG retrieval tests — pure cosine math + retrieval filters on SQLite."""

import pytest

from src.db.models import Session, Turn, User
from src.models.rag_retrieval import cosine, retrieve_effective_reframes


def test_cosine_basics():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)
    assert cosine([0, 0], [1, 0]) == 0.0  # zero vector -> no similarity, no crash


def _seed_exchange(db, user_id, cfi_before, cfi_after, embedding, base_idx=0,
                   session=None):
    session = session or Session(user_id=user_id)
    db.add(session)
    db.flush()
    db.add(Turn(session_id=session.id, turn_idx=base_idx, role="client",
                text="I always mess up", cfi=cfi_before, distortions={},
                embedding=embedding))
    db.add(Turn(session_id=session.id, turn_idx=base_idx + 1, role="counselor",
                text="What would count as evidence against that?"))
    db.add(Turn(session_id=session.id, turn_idx=base_idx + 2, role="client",
                text="Well, maybe not always", cfi=cfi_after, distortions={}))
    db.commit()
    return session


def test_retrieves_only_cfi_lowering_exchanges(db_session):
    user = User(email="rag@example.com")
    db_session.add(user)
    db_session.flush()

    _seed_exchange(db_session, user.id, cfi_before=0.8, cfi_after=0.5,
                   embedding=[1.0, 0.0])          # worked
    _seed_exchange(db_session, user.id, cfi_before=0.5, cfi_after=0.7,
                   embedding=[1.0, 0.0])          # made things worse -> excluded

    results = retrieve_effective_reframes(db_session, user.id, [1.0, 0.0], k=5)
    assert len(results) == 1
    assert results[0]["cfi_drop"] == pytest.approx(0.3)
    assert "evidence against" in results[0]["counselor_text"]


def test_no_cross_user_leakage(db_session):
    alice = User(email="alice@example.com")
    bob = User(email="bob@example.com")
    db_session.add_all([alice, bob])
    db_session.flush()
    _seed_exchange(db_session, alice.id, 0.8, 0.4, [1.0, 0.0])

    assert retrieve_effective_reframes(db_session, bob.id, [1.0, 0.0]) == []


def test_similarity_floor(db_session):
    user = User(email="floor@example.com")
    db_session.add(user)
    db_session.flush()
    _seed_exchange(db_session, user.id, 0.8, 0.4, [1.0, 0.0])

    # orthogonal query -> below min_similarity -> nothing returned
    assert retrieve_effective_reframes(db_session, user.id, [0.0, 1.0]) == []
