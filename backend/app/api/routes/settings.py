from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.auth.deps import get_current_user, enforce_csrf
from app.core.idempotency import enforce_idempotency
from app.models.user import User
from app.models.design import UserSettings
from pydantic import BaseModel, Field

router = APIRouter(prefix="/users/me/settings", tags=["settings"])

class UserSettingsResponse(BaseModel):
    theme: str
    default_mode: str

class UpdateSettingsRequest(BaseModel):
    theme: str | None = Field(default=None, max_length=20)
    default_mode: str | None = Field(default=None, max_length=20)

@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if not settings:
        # Create default
        settings = UserSettings(user_id=user.id, theme="system", default_mode="product")
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return UserSettingsResponse(theme=settings.theme, default_mode=settings.default_mode)  # type: ignore


@router.patch("", response_model=UserSettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    await enforce_idempotency("user-settings-update", str(user.id), idempotency_key, 180)
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if not settings:
        settings = UserSettings(user_id=user.id, theme="system", default_mode="product")
        db.add(settings)

    if request.theme is not None:
        settings.theme = request.theme
    if request.default_mode is not None:
        settings.default_mode = request.default_mode

    db.commit()
    db.refresh(settings)

    return UserSettingsResponse(theme=settings.theme, default_mode=settings.default_mode)  # type: ignore
