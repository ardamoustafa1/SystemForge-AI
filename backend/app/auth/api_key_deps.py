from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models import UserSettings
from app.core.security import verify_password

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key_header: str = Security(api_key_header), db: Session = Depends(get_db)) -> User:
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )

    if not api_key_header.startswith("sf_") or len(api_key_header) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    last4 = api_key_header[-4:]

    # We must scan users that have an active API key with this last4.
    # In a larger system we'd use Redis or a dedicated API key table.
    # Here, we lookup by last4 to avoid full table scans of bcrypt hashes.
    possible_settings = (
        db.query(UserSettings)
        .filter(UserSettings.api_key_last4 == last4, UserSettings.api_key_revoked_at.is_(None))
        .all()
    )

    for setting in possible_settings:
        if setting.api_key_hash and verify_password(api_key_header, setting.api_key_hash):
            user = db.query(User).filter(User.id == setting.user_id, User.is_active.is_(True)).first()
            if user:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or revoked API key",
    )
