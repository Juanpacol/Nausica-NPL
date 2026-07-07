"""FastAPI auth dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session as OrmSession

from src.auth.jwt import decode_token
from src.db.models import OrgMembership, User
from src.db.session import get_db

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: OrmSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user


def require_clinician_of(db: OrmSession, clinician: User, patient: User) -> None:
    """403 unless `clinician` shares an org with `patient` with a clinician/admin
    role AND the patient has opted in to clinician view. Self-access always allowed."""
    if clinician.id == patient.id:
        return
    if not patient.consent_clinician_view:
        raise HTTPException(status_code=403, detail="Patient has not granted clinician access")
    patient_orgs = {
        m.org_id for m in db.query(OrgMembership).filter_by(user_id=patient.id)
    }
    allowed = (
        db.query(OrgMembership)
        .filter(
            OrgMembership.user_id == clinician.id,
            OrgMembership.org_id.in_(patient_orgs),
            OrgMembership.role.in_(["clinician", "admin"]),
        )
        .first()
    )
    if allowed is None:
        raise HTTPException(status_code=403, detail="Not a clinician for this patient")
