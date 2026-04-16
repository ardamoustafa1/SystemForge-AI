from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import enforce_csrf, get_current_user
from app.auth.service import login_user, register_user, rotate_refresh_token, list_active_sessions, revoke_session
from app.core.config import get_settings
from app.core.rate_limiter import clear_rate_limit, enforce_rate_limit
from app.db.session import get_db
from app.models import User, RefreshTokenSession
from app.schemas.auth import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest
from app.services.security_audit_service import log_security_audit
from app.core.async_bridge import run_async

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
        path="/",
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
    db.query(RefreshTokenSession).filter(RefreshTokenSession.user_id == user.id, RefreshTokenSession.is_revoked.is_(False)).update(
        {"is_revoked": True}
    )
    db.commit()
    run_async(log_security_audit("auth.logout_all_sessions", actor_user_id=user.id, workspace_id=user.default_workspace_id, metadata={}))
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name, path="/")
    response.delete_cookie(settings.refresh_cookie_name, path="/")
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
        path="/",
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
    run_async(log_security_audit("auth.revoke_session", actor_user_id=user.id, workspace_id=user.default_workspace_id, metadata={"session_id": session_id}))
    return {"ok": True}
