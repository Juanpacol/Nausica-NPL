"""DB model tests — in-memory SQLite, no Postgres or network required."""

from src.db.models import NoteAnalysis, Organization, OrgMembership, Session, Turn, User


def test_user_session_turn_roundtrip(db_session):
    user = User(email="a@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()

    session = Session(user_id=user.id)
    db_session.add(session)
    db_session.flush()

    db_session.add(Turn(session_id=session.id, turn_idx=0, role="client",
                        text="I always fail", distortions={"all_or_nothing": 0.8}, cfi=0.7))
    db_session.add(Turn(session_id=session.id, turn_idx=1, role="counselor",
                        text="What makes you say always?"))
    db_session.commit()

    loaded = db_session.get(Session, session.id)
    assert len(loaded.turns) == 2
    assert loaded.turns[0].role == "client" and loaded.turns[0].cfi == 0.7
    assert loaded.turns[1].distortions is None  # counselor turns carry no scores


def test_turns_ordered_by_idx(db_session):
    user = User(email="b@example.com")
    db_session.add(user)
    db_session.flush()
    session = Session(user_id=user.id)
    db_session.add(session)
    db_session.flush()
    # insert out of order
    for idx in (2, 0, 1):
        db_session.add(Turn(session_id=session.id, turn_idx=idx, role="client", text=f"t{idx}"))
    db_session.commit()
    db_session.expire_all()
    assert [t.turn_idx for t in db_session.get(Session, session.id).turns] == [0, 1, 2]


def test_note_analysis_unique_per_file(db_session):
    user = User(email="c@example.com")
    db_session.add(user)
    db_session.flush()
    db_session.add(NoteAnalysis(user_id=user.id, source="obsidian", file_hash="abc",
                                distortions={}, cfi=0.5))
    db_session.commit()
    row = (db_session.query(NoteAnalysis)
           .filter_by(user_id=user.id, source="obsidian", file_hash="abc").first())
    assert row is not None and row.cfi == 0.5


def test_consent_defaults_false(db_session):
    user = User(email="d@example.com")
    db_session.add(user)
    db_session.commit()
    assert user.consent_clinician_view is False


def test_org_membership_roles(db_session):
    org = Organization(name="Clinic A")
    clinician = User(email="doc@example.com")
    patient = User(email="pat@example.com")
    db_session.add_all([org, clinician, patient])
    db_session.flush()
    db_session.add_all([
        OrgMembership(user_id=clinician.id, org_id=org.id, role="clinician"),
        OrgMembership(user_id=patient.id, org_id=org.id, role="patient"),
    ])
    db_session.commit()
    roles = {m.role for m in db_session.get(Organization, org.id).memberships}
    assert roles == {"clinician", "patient"}
