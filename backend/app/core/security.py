from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import bcrypt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_minutes: int | None = None, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire_delta = expires_minutes or settings.jwt_exp_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expire_delta)
    payload: dict[str, Any] = {"sub": subject, "exp": expire_at}
    if extra:
        payload.update(extra)
    if settings.jwt_private_key and settings.jwt_algorithm == "RS256":
        return jwt.encode(payload, settings.jwt_private_key, algorithm="RS256")
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
