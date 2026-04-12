import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest


def register_user(payload: RegisterRequest, db: Session) -> CurrentUserResponse:
    normalized_email = payload.email.lower().strip()
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name)


def login_user(payload: LoginRequest, db: Session) -> tuple[AuthResponse, str]:
    normalized_email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized_email))

    invalid_credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(subject=str(user.id))
    settings = get_settings()
    return AuthResponse(
        user=CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name),
        csrf_token=secrets.token_urlsafe(32),
        expires_in_seconds=settings.jwt_exp_minutes * 60,
    ), access_token
