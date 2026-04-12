from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.redis import close_redis_client, get_redis_client
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401

logger = logging.getLogger("systemforge.startup")


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    # Eagerly initialize shared infra clients so startup failures are explicit.
    get_redis_client()
    settings = get_settings()
    if settings.auto_create_tables:
        if settings.app_env.lower() not in {"development", "dev", "test"}:
            raise RuntimeError(
                "AUTO_CREATE_TABLES is only allowed in development/test. "
                "Use Alembic migrations for staging/production."
            )
        logger.warning("AUTO_CREATE_TABLES enabled; this must remain disabled in production.")
        Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        await close_redis_client()
