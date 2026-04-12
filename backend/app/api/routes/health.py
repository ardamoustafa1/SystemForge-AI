from fastapi import APIRouter, Depends
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep, redis_dep

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
