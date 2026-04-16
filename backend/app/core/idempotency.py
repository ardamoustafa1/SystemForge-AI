from __future__ import annotations

from fastapi import HTTPException, status

from app.core.redis import get_redis_client


async def enforce_idempotency(scope: str, owner_key: str, idempotency_key: str | None, ttl_seconds: int = 300) -> None:
    if not idempotency_key:
        return
    redis = get_redis_client()
    key = f"idempotency:{scope}:{owner_key}:{idempotency_key.strip()}"
    try:
        created = await redis.set(key, "1", ex=ttl_seconds, nx=True)
    except Exception:
        return
    if not created:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate request detected for this idempotency key",
        )

