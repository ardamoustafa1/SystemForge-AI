from fastapi import APIRouter, Depends, Response
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep, redis_dep
from app.core.config import get_settings
from app.core.metrics import render_prometheus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/ready")
async def readiness(
    db: Session = Depends(db_session_dep),
    redis_client: redis.Redis = Depends(redis_dep),
):
    db.execute(text("SELECT 1"))
    await redis_client.ping()
    return {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}


@router.get("/metrics")
def metrics():
    return Response(content=render_prometheus(), media_type="text/plain; version=0.0.4")


@router.get("/api-versions")
def api_versions():
    settings = get_settings()
    return {
        "current": settings.api_version,
        "deprecation_policy_url": settings.api_deprecation_policy_url,
        "deprecated_after": settings.api_deprecated_after or None,
        "sunset_at": settings.api_sunset_at or None,
        "compatibility": "semver-compatible additive changes within major versions",
    }
