from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.redis import get_redis_client


def _job_list_key(workspace_id: int, user_id: int) -> str:
    return f"jobs:center:{workspace_id}:{user_id}"


async def track_job(workspace_id: int, user_id: int, payload: dict) -> None:
    redis = get_redis_client()
    item = {
        "tracked_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    key = _job_list_key(workspace_id, user_id)
    await redis.lpush(key, json.dumps(item))
    await redis.ltrim(key, 0, 99)
    await redis.expire(key, 60 * 60 * 24 * 30)


async def list_jobs(workspace_id: int, user_id: int) -> list[dict]:
    redis = get_redis_client()
    key = _job_list_key(workspace_id, user_id)
    rows = await redis.lrange(key, 0, 99)
    out: list[dict] = []
    for row in rows:
        raw = row.decode("utf-8") if isinstance(row, bytes) else str(row)
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out

