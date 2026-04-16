from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.redis import get_redis_client


async def record_abuse_event(event_type: str, actor: str, severity: int, metadata: dict[str, str] | None = None) -> None:
    redis = get_redis_client()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"abuse:counter:{ts}:{event_type}"
    try:
        await redis.incrby(key, 1)
        await redis.expire(key, 60 * 60 * 24 * 30)
        if severity >= 70:
            await redis.incrby(f"abuse:counter:{ts}:high-severity", 1)
        payload = {"type": event_type, "actor": actor, "severity": severity, "metadata": metadata or {}}
        await redis.xadd("abuse:events", {"payload_json": json.dumps(payload)}, maxlen=50000, approximate=True)
    except Exception:
        return


async def get_abuse_summary(days: int = 7) -> dict[str, int]:
    redis = get_redis_client()
    totals: dict[str, int] = {"high_severity": 0}
    now = datetime.now(timezone.utc)
    for i in range(max(1, days)):
        day = (now).replace(hour=0, minute=0, second=0, microsecond=0)
        day = day.timestamp() - (i * 86400)
        day_str = datetime.fromtimestamp(day, tz=timezone.utc).strftime("%Y-%m-%d")
        try:
            cursor = 0
            pattern = f"abuse:counter:{day_str}:*"
            while True:
                cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=200)
                for key in keys:
                    key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
                    value = int(await redis.get(key) or 0)
                    metric = key_str.split(":")[-1].replace("-", "_")
                    totals[metric] = totals.get(metric, 0) + value
                if cursor == 0:
                    break
        except Exception:
            continue
    return totals

