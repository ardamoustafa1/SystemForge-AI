from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.services.abuse_analytics_service import record_abuse_event

_memory_bucket: dict[str, tuple[int, datetime]] = {}
_memory_quota: dict[str, tuple[int, datetime]] = {}


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
            await record_abuse_event(event_type="rate-limit", actor=identifier, severity=55, metadata={"scope": scope})
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
            await record_abuse_event(event_type="rate-limit", actor=identifier, severity=45, metadata={"scope": scope, "fallback": "memory"})
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


async def enforce_usage_quota(
    scope: str,
    identifier: str,
    consume_units: int,
    max_units: int,
    window_seconds: int = 86400,
) -> int:
    if consume_units <= 0:
        return max_units
    key = f"quota:{scope}:{identifier}"
    try:
        redis = get_redis_client()
        current = await redis.incrby(key, consume_units)
        if current == consume_units:
            await redis.expire(key, window_seconds)
        if current > max_units:
            await record_abuse_event(event_type="quota-exceeded", actor=identifier, severity=70, metadata={"scope": scope})
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Usage quota exceeded",
            )
        return max(0, max_units - int(current))
    except HTTPException:
        raise
    except Exception:
        now = datetime.now(timezone.utc)
        current, expires_at = _memory_quota.get(key, (0, now + timedelta(seconds=window_seconds)))
        if now >= expires_at:
            current = 0
            expires_at = now + timedelta(seconds=window_seconds)
        current += consume_units
        _memory_quota[key] = (current, expires_at)
        if current > max_units:
            await record_abuse_event(event_type="quota-exceeded", actor=identifier, severity=60, metadata={"scope": scope, "fallback": "memory"})
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Usage quota exceeded",
            )
        return max(0, max_units - current)
