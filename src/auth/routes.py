"""Auth endpoints: register + login (email/password → JWT).

Google OAuth is deliberately a stub for now — it needs client credentials the
project doesn't have yet; the schema (`User.auth_provider`) is ready for it.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session as OrmSession

from src.auth.jwt import create_access_token, hash_password, verify_password
from src.db.models import User
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: OrmSession = Depends(get_db)):
    if db.query(User).filter_by(email=req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id), user_id=user.id)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: OrmSession = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email).first()
    if user is None or user.password_hash is None or not verify_password(
        req.password, user.password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id), user_id=user.id)
