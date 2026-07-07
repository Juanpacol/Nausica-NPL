"""JWT creation/verification + password hashing.

Secret comes from env NAUSICA_JWT_SECRET (see .env.example). The dev fallback is
deliberately obvious so nobody ships it: startup logs a warning when it's in use.
Tokens are long-lived by default (30 days) — appropriate for a personal journaling
tool where re-login friction hurts more than token-rotation buys; revisit before
any multi-tenant clinical deployment.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_DAYS = 30

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _secret() -> str:
    secret = os.environ.get("NAUSICA_JWT_SECRET")
    if not secret:
        logger.warning("NAUSICA_JWT_SECRET not set — using INSECURE dev secret")
        secret = "dev-only-insecure-secret"
    return secret


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_DAYS)
    return jwt.encode({"sub": user_id, "exp": expires}, _secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    """Return the user_id, or None if the token is invalid/expired."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
