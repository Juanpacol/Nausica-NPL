"""Auth tests: JWT round-trip, password hashing, register/login endpoints, and
the clinician-consent gate. Endpoints tested with dependency overrides on SQLite."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.auth.dependencies import require_clinician_of
from src.auth.jwt import create_access_token, decode_token, hash_password, verify_password
from src.db.models import Organization, OrgMembership, User


def test_password_hash_roundtrip():
    h = hash_password("s3cret-pass")
    assert h != "s3cret-pass"
    assert verify_password("s3cret-pass", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    token = create_access_token("user-123")
    assert decode_token(token) == "user-123"
    assert decode_token(token + "tampered") is None
    assert decode_token("garbage") is None


@pytest.fixture
def client(db_session):
    from src.api.main import app
    from src.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_register_login_flow(client):
    r = client.post("/auth/register", json={"email": "x@example.com", "password": "longenough"})
    assert r.status_code == 201
    token = r.json()["access_token"]
    assert decode_token(token) == r.json()["user_id"]

    # duplicate email rejected
    r2 = client.post("/auth/register", json={"email": "x@example.com", "password": "longenough"})
    assert r2.status_code == 409

    r3 = client.post("/auth/login", json={"email": "x@example.com", "password": "longenough"})
    assert r3.status_code == 200

    r4 = client.post("/auth/login", json={"email": "x@example.com", "password": "wrongwrong"})
    assert r4.status_code == 401


def test_protected_endpoint_requires_token(client):
    r = client.post("/analyze", json={"text": "hello"})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "y@example.com", "password": "short"})
    assert r.status_code == 422


def _seed_org(db, consent: bool):
    org = Organization(name="Clinic")
    doc = User(email="doc@x.com")
    pat = User(email="pat@x.com", consent_clinician_view=consent)
    db.add_all([org, doc, pat])
    db.flush()
    db.add_all([
        OrgMembership(user_id=doc.id, org_id=org.id, role="clinician"),
        OrgMembership(user_id=pat.id, org_id=org.id, role="patient"),
    ])
    db.commit()
    return doc, pat


def test_clinician_gate_requires_consent(db_session):
    doc, pat = _seed_org(db_session, consent=False)
    with pytest.raises(HTTPException) as exc:
        require_clinician_of(db_session, doc, pat)
    assert exc.value.status_code == 403


def test_clinician_gate_allows_with_consent(db_session):
    doc, pat = _seed_org(db_session, consent=True)
    require_clinician_of(db_session, doc, pat)  # no exception


def test_clinician_gate_self_access_always_ok(db_session):
    user = User(email="me@x.com", consent_clinician_view=False)
    db_session.add(user)
    db_session.commit()
    require_clinician_of(db_session, user, user)  # no exception
