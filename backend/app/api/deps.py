from collections.abc import AsyncIterator, Iterator

import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.core.redis import get_redis
from app.db.session import get_db


def db_session_dep() -> Iterator[Session]:
    yield from get_db()


async def redis_dep() -> AsyncIterator[redis.Redis]:
    async for client in get_redis():
        yield client
