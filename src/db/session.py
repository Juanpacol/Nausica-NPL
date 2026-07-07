"""Engine + FastAPI session dependency.

DATABASE_URL resolution (first match wins):
1. env DATABASE_URL (production / docker-compose)
2. local default: postgresql+psycopg://localhost/nausica (Homebrew Postgres)

Tests override `get_db` with an in-memory SQLite session — see tests/conftest.py.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker

DEFAULT_URL = "postgresql+psycopg://localhost/nausica"


@lru_cache(maxsize=1)
def get_engine():
    url = os.environ.get("DATABASE_URL", DEFAULT_URL)
    return create_engine(url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Generator[OrmSession, None, None]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
