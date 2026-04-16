from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.redis import get_redis_client


async def log_security_audit(action: str, actor_user_id: int, workspace_id: int | None, metadata: dict | None = None) -> None:
    redis = get_redis_client()
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor_user_id": actor_user_id,
        "workspace_id": workspace_id,
        "metadata": metadata or {},
    }
    try:
        await redis.xadd("security:audit:events", {"payload_json": json.dumps(payload)}, maxlen=100000, approximate=True)
    except Exception:
        return


async def list_security_audit(limit: int = 200) -> list[dict]:
    redis = get_redis_client()
    out: list[dict] = []
    try:
        rows = await redis.xrevrange("security:audit:events", count=limit)
    except Exception:
        return out
    for _, fields in rows:
        raw = fields.get("payload_json", "{}")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out

