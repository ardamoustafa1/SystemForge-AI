from __future__ import annotations

import json

from app.core.redis import get_redis_client


def _key(workspace_id: int) -> str:
    return f"workspace:template-policy:{workspace_id}"


async def get_template_policy(workspace_id: int) -> dict:
    redis = get_redis_client()
    raw = await redis.get(_key(workspace_id))
    if not raw:
        return {
            "workspace_id": workspace_id,
            "template_name": "default",
            "required_stack_keywords": [],
            "forbidden_patterns": [],
            "security_baseline": ["encryption-at-rest", "least-privilege", "audit-logging"],
        }
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


async def update_template_policy(workspace_id: int, payload: dict) -> dict:
    redis = get_redis_client()
    doc = {"workspace_id": workspace_id, **payload}
    await redis.set(_key(workspace_id), json.dumps(doc), ex=60 * 60 * 24 * 30)
    return doc

