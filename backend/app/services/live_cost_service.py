from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.redis import get_redis_client


def _pricing_key() -> str:
    return "cost:pricing:cloud"


def _usage_key(workspace_id: int) -> str:
    return f"cost:usage:workspace:{workspace_id}"


async def sync_cloud_pricing() -> dict:
    """Placeholder cloud pricing sync cache (extensible to AWS/GCP APIs)."""
    redis = get_redis_client()
    payload = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["aws-sample", "gcp-sample"],
        "compute_index": 1.03,
        "storage_index": 1.01,
        "network_index": 1.05,
    }
    await redis.set(_pricing_key(), json.dumps(payload), ex=60 * 60 * 6)
    return payload


async def get_cloud_pricing() -> dict:
    redis = get_redis_client()
    raw = await redis.get(_pricing_key())
    if not raw:
        return await sync_cloud_pricing()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


async def report_workspace_usage(workspace_id: int, monthly_actual_usd: int, source: str) -> dict:
    redis = get_redis_client()
    payload = {
        "workspace_id": workspace_id,
        "monthly_actual_usd": monthly_actual_usd,
        "source": source,
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }
    await redis.set(_usage_key(workspace_id), json.dumps(payload), ex=60 * 60 * 24 * 31)
    return payload


async def get_workspace_usage(workspace_id: int) -> dict | None:
    redis = get_redis_client()
    raw = await redis.get(_usage_key(workspace_id))
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)

