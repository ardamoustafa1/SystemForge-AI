from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.deps import enforce_csrf, get_current_user
from app.auth.service import login_user, register_user
from app.core.config import get_settings
from app.core.rate_limiter import clear_rate_limit, enforce_rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest

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
    auth_payload, access_token = login_user(payload=payload, db=db)
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
    return auth_payload


@router.post("/logout")
def logout(
    response: Response,
    _: None = Depends(enforce_csrf),
):
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)):
    return CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name)
