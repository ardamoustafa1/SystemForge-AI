from collections.abc import AsyncIterator, Iterator

import redis.asyncio as redis
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.redis import get_redis
from app.db.session import get_db
from app.core.config import get_settings, Settings


def db_session_dep() -> Iterator[Session]:
    yield from get_db()


async def redis_dep() -> AsyncIterator[redis.Redis]:
    async for client in get_redis():
        yield client

# Dependency Injection for settings to allow test overriding via app.dependency_overrides
def settings_dep() -> Settings:
    return get_settings()
