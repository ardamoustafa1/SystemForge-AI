import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, RefreshTokenSession
from app.schemas.auth import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest


def register_user(payload: RegisterRequest, db: Session) -> CurrentUserResponse:
    from app.models import Workspace, WorkspaceMember, RoleEnum  # local import to avoid circular deps

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
    db.flush()  # get user.id

    # Create a personal default workspace for the new user
    workspace = Workspace(name=f"{payload.full_name.strip()}'s Workspace")
    db.add(workspace)
    db.flush()

    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=RoleEnum.admin))
    user.default_workspace_id = workspace.id

    db.commit()
    db.refresh(user)
    return CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name, default_workspace_id=user.default_workspace_id)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_refresh_session(db: Session, user: User) -> str:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(48)
    session = RefreshTokenSession(
        user_id=user.id,
        token_hash=_hash_refresh_token(raw_token),
        is_revoked=False,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_exp_days),
    )
    db.add(session)
    db.flush()
    return raw_token


def login_user(payload: LoginRequest, db: Session) -> tuple[AuthResponse, str, str]:
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

    access_token = create_access_token(subject=str(user.id), extra={"tv": int(user.token_version)})
    refresh_token = _issue_refresh_session(db=db, user=user)
    db.commit()
    settings = get_settings()
    return AuthResponse(
        user=CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name),
        csrf_token=secrets.token_urlsafe(32),
        expires_in_seconds=settings.jwt_exp_minutes * 60,
    ), access_token, refresh_token


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[AuthResponse, str, str]:
    token_hash = _hash_refresh_token(refresh_token)
    session = db.scalar(select(RefreshTokenSession).where(RefreshTokenSession.token_hash == token_hash))
    if not session or session.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if session.expires_at < datetime.now(timezone.utc):
        session.is_revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        session.is_revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    session.is_revoked = True
    session.rotated_at = datetime.now(timezone.utc)
    access_token = create_access_token(subject=str(user.id), extra={"tv": int(user.token_version)})
    new_refresh = _issue_refresh_session(db=db, user=user)
    settings = get_settings()
    db.commit()
    return (
        AuthResponse(
            user=CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name, default_workspace_id=user.default_workspace_id),
            csrf_token=secrets.token_urlsafe(32),
            expires_in_seconds=settings.jwt_exp_minutes * 60,
        ),
        access_token,
        new_refresh,
    )


def list_active_sessions(db: Session, user: User) -> list[dict]:
    rows = (
        db.query(RefreshTokenSession)
        .filter(RefreshTokenSession.user_id == user.id)
        .order_by(RefreshTokenSession.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": row.id,
            "is_revoked": bool(row.is_revoked),
            "created_at": row.created_at,
            "expires_at": row.expires_at,
            "rotated_at": row.rotated_at,
        }
        for row in rows
    ]


def revoke_session(db: Session, user: User, session_id: int) -> None:
    row = db.scalar(select(RefreshTokenSession).where(RefreshTokenSession.id == session_id, RefreshTokenSession.user_id == user.id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    row.is_revoked = True
    db.commit()
