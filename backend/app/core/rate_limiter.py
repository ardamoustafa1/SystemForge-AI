from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.redis import get_redis_client

_memory_bucket: dict[str, tuple[int, datetime]] = {}


async def enforce_rate_limit(scope: str, identifier: str, limit: int, window_seconds: int = 60) -> None:
    if get_settings().app_env.lower() in {"test", "testing"}:
        return
    key = f"ratelimit:{scope}:{identifier}"
    try:
        redis = get_redis_client()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        return
    except HTTPException:
        raise
    except Exception:
        now = datetime.now(timezone.utc)
        current, expires_at = _memory_bucket.get(key, (0, now + timedelta(seconds=window_seconds)))
        if now >= expires_at:
            current = 0
            expires_at = now + timedelta(seconds=window_seconds)
        current += 1
        _memory_bucket[key] = (current, expires_at)
        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )


async def clear_rate_limit(scope: str, identifier: str) -> None:
    key = f"ratelimit:{scope}:{identifier}"
    try:
        redis = get_redis_client()
        await redis.delete(key)
    except Exception:
        _memory_bucket.pop(key, None)
