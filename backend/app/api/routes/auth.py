from fastapi import APIRouter, Depends, Request, Response, status, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import secrets
import logging
import re
from datetime import datetime, timezone

from app.auth.deps import enforce_csrf, get_current_user
from app.auth.service import login_user, register_user, rotate_refresh_token, list_active_sessions, revoke_session
from app.core.config import get_settings
from app.core.rate_limiter import clear_rate_limit, enforce_rate_limit
from app.db.session import get_db
from app.models import User, RefreshTokenSession, UserSettings
from app.schemas.auth import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest
from pydantic import BaseModel
from app.services.security_audit_service import log_security_audit
from app.core.async_bridge import run_async
from app.core.security import hash_password, verify_password
from app.core.redis import get_redis_client
from app.core.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="auth-register", identifier=client_ip, limit=8, window_seconds=60)
    return register_user(payload=payload, db=db)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="auth-login-ip", identifier=client_ip, limit=20, window_seconds=60)
    attempt_key = f"{payload.email.lower().strip()}:{client_ip}"
    await enforce_rate_limit(scope="auth-login-attempt", identifier=attempt_key, limit=10, window_seconds=900)
    auth_payload, access_token, refresh_token = login_user(payload=payload, db=db)
    await clear_rate_limit(scope="auth-login-attempt", identifier=attempt_key)

    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=auth_payload.expires_in_seconds,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=auth_payload.csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=auth_payload.expires_in_seconds,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_exp_days * 24 * 60 * 60,
        path="/api/auth/refresh",
    )
    return auth_payload


@router.post("/logout")
def logout(
    response: Response,
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.token_version = int(user.token_version) + 1
    db.query(RefreshTokenSession).filter(
        RefreshTokenSession.user_id == user.id, RefreshTokenSession.is_revoked.is_(False)
    ).update({"is_revoked": True})
    db.commit()
    run_async(
        log_security_audit(
            "auth.logout_all_sessions", actor_user_id=user.id, workspace_id=user.default_workspace_id, metadata={}
        )
    )
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name, path="/")
    response.delete_cookie(settings.refresh_cookie_name, path="/api/auth/refresh")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    return {"ok": True}


@router.post("/refresh", response_model=AuthResponse)
async def refresh_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is required")
    auth_payload, access_token, rotated_refresh_token = rotate_refresh_token(db=db, refresh_token=refresh_token)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=auth_payload.expires_in_seconds,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=auth_payload.csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=auth_payload.expires_in_seconds,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=rotated_refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_exp_days * 24 * 60 * 60,
        path="/api/auth/refresh",
    )
    return auth_payload


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)):
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        default_workspace_id=user.default_workspace_id,
    )


class UpdateUserRequest(BaseModel):
    full_name: str | None = None


@router.patch("/me", response_model=CurrentUserResponse)
def update_me(
    payload: UpdateUserRequest,
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None and payload.full_name.strip():
        user.full_name = payload.full_name.strip()
        db.commit()
        db.refresh(user)
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        default_workspace_id=user.default_workspace_id,
    )


@router.get("/sessions")
def list_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": list_active_sessions(db, user)}


@router.delete("/sessions/{session_id}")
def revoke_user_session(
    session_id: int,
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_session(db, user, session_id)
    run_async(
        log_security_audit(
            "auth.revoke_session",
            actor_user_id=user.id,
            workspace_id=user.default_workspace_id,
            metadata={"session_id": session_id},
        )
    )
    return {"ok": True}


class GenerateApiKeyResponse(BaseModel):
    api_key: str


@router.post("/api-keys", response_model=GenerateApiKeyResponse)
async def generate_api_key(
    request: Request,
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="auth-apikey-generate", identifier=str(user.id), limit=5, window_seconds=86400)
    
    api_key = f"sf_{secrets.token_urlsafe(32)}"
    api_key_hash = hash_password(api_key)
    last4 = api_key[-4:]

    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    settings.api_key_hash = api_key_hash
    settings.api_key_last4 = last4
    settings.api_key_created_at = datetime.now(timezone.utc)
    settings.api_key_revoked_at = None
    db.commit()

    run_async(
        log_security_audit(
            "auth.generate_api_key",
            actor_user_id=user.id,
            workspace_id=user.default_workspace_id,
            metadata={"last4": last4},
        )
    )
    return GenerateApiKeyResponse(api_key=api_key)


class ApiKeyStatusResponse(BaseModel):
    last4: str | None
    created_at: str | None
    revoked_at: str | None


@router.get("/api-keys", response_model=ApiKeyStatusResponse)
def get_api_key_status(
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings or not settings.api_key_last4:
        return ApiKeyStatusResponse(last4=None, created_at=None, revoked_at=None)

    return ApiKeyStatusResponse(
        last4=settings.api_key_last4,
        created_at=settings.api_key_created_at.isoformat() if settings.api_key_created_at else None,
        revoked_at=settings.api_key_revoked_at.isoformat() if settings.api_key_revoked_at else None,
    )


@router.delete("/api-keys")
def revoke_api_key(
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings and settings.api_key_hash:
        settings.api_key_revoked_at = datetime.now(timezone.utc)
        db.commit()
        run_async(
            log_security_audit(
                "auth.revoke_api_key",
                actor_user_id=user.id,
                workspace_id=user.default_workspace_id,
                metadata={"last4": settings.api_key_last4},
            )
        )
    return {"ok": True}


class ResetPasswordRequest(BaseModel):
    email: str


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="auth-password-reset", identifier=client_ip, limit=3, window_seconds=3600)
    
    logger = logging.getLogger("systemforge.auth")
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if user:
        token = secrets.token_urlsafe(32)
        redis_client = get_redis_client()
        await redis_client.setex(f"pwd_reset:{token}", 3600, user.id)
        
        background_tasks.add_task(send_password_reset_email, payload.email, token)

    return {"ok": True, "message": "If the email exists, a password reset link has been sent."}


class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password/confirm")
async def reset_password_confirm(payload: ResetPasswordConfirmRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="auth-password-reset-confirm", identifier=client_ip, limit=5, window_seconds=3600)
    
    if (
        len(payload.new_password) < 8
        or not re.search(r"[A-Za-z]", payload.new_password)
        or not re.search(r"[0-9]", payload.new_password)
    ):
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters and contain letters and numbers"
        )

    redis_client = get_redis_client()
    user_id_str = await redis_client.get(f"pwd_reset:{payload.token}")
    if not user_id_str:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    user.token_version = int(user.token_version) + 1
    db.commit()

    await redis_client.delete(f"pwd_reset:{payload.token}")
    run_async(
        log_security_audit(
            "auth.password_reset", actor_user_id=user.id, workspace_id=user.default_workspace_id, metadata={}
        )
    )

    return {"ok": True, "message": "Password has been successfully reset"}


@router.delete("/account")
async def delete_account(
    payload: LoginRequest,
    request: Request,
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="auth-delete-account", identifier=str(user.id), limit=3, window_seconds=86400)
    
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password confirmation")

    user.is_active = False
    user.token_version = int(user.token_version) + 1
    db.commit()
    run_async(
        log_security_audit(
            "auth.account_deleted",
            actor_user_id=user.id,
            workspace_id=user.default_workspace_id,
            metadata={"action": "soft_delete_gdpr"},
        )
    )
    return {"ok": True, "message": "Account scheduled for deletion"}
