"""SQLAlchemy models (Phase 3) — the persistent core of the product.

Replaces the in-memory `_sessions` dict in src/api/main.py. Multi-tenant from day
one (Organization + OrgMembership with patient/clinician/admin roles) so the
clinician-dashboard and consent flows in later phases are schema-ready, not a
migration crisis.

Privacy notes baked into the schema:
- `User.consent_clinician_view` is opt-in (default False) — a clinician sees a
  patient's data only while this is True; revoking hides it again.
- `Turn.clinician_feedback_*` (Phase 7) captures reframe quality judgments for a
  future DPO export; nullable, never required.
- No raw note content from Obsidian is stored — only `file_hash` + derived scores
  (NoteAnalysis), consistent with the local-first story.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    memberships: Mapped[list["OrgMembership"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # null for OAuth-only accounts
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), default="local")  # local | google
    consent_clinician_view: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    memberships: Mapped[list["OrgMembership"]] = relationship(back_populates="user")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")


class OrgMembership(Base):
    __tablename__ = "org_memberships"
    __table_args__ = (UniqueConstraint("user_id", "org_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # patient | clinician | admin

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")


class Session(Base):
    """One reframing conversation (was a key in the in-memory _sessions dict)."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="sessions")
    turns: Mapped[list["Turn"]] = relationship(
        back_populates="session", order_by="Turn.turn_idx"
    )


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_idx", "role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    turn_idx: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(12))  # client | counselor
    text: Mapped[str] = mapped_column(Text)
    # distortions + cfi only on client turns; counselor turns leave them null
    distortions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cfi: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Phase 7: clinician feedback for future DPO export — always optional
    clinician_feedback_good: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    clinician_feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase 6 RAG: MiniLM embedding of client turns (384 floats as JSON).
    # Cosine retrieval runs in Python — fine at prototype scale; the pgvector
    # migration path is documented in docker-compose.yml (pgvector/pgvector image).
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)

    session: Mapped[Session] = relationship(back_populates="turns")


class NoteAnalysis(Base):
    """A one-shot /analyze result outside a reframing session (e.g. Obsidian plugin).

    Stores derived scores only — never the note's raw text (local-first promise)."""

    __tablename__ = "note_analyses"
    __table_args__ = (UniqueConstraint("user_id", "source", "file_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[str] = mapped_column(String(20), default="api")  # api | obsidian | mobile
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    distortions: Mapped[dict] = mapped_column(JSON)
    cfi: Mapped[float] = mapped_column(Float)
    rigidity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    archetype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
