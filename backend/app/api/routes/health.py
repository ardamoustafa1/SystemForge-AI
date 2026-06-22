from fastapi import APIRouter, Depends, Header, HTTPException, Response
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep, redis_dep, settings_dep
from app.core.config import Settings
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


@router.get("/metrics", include_in_schema=False)
def metrics(
    x_metrics_token: str | None = Header(default=None),
    settings: Settings = Depends(settings_dep)
):
    if x_metrics_token != settings.metrics_secret:
        raise HTTPException(status_code=401, detail="Unauthorized metrics access")
    return Response(content=render_prometheus(), media_type="text/plain; version=0.0.4")


@router.get("/api-versions")
def api_versions(settings: Settings = Depends(settings_dep)):
    return {
        "current": settings.api_version,
        "deprecation_policy_url": settings.api_deprecation_policy_url,
        "deprecated_after": settings.api_deprecated_after or None,
        "sunset_at": settings.api_sunset_at or None,
        "compatibility": "semver-compatible additive changes within major versions",
    }
