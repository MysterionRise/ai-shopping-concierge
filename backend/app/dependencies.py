from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.core.database import async_session_factory
from app.core.redis import get_redis_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_redis() -> aioredis.Redis:
    """Return a Redis client backed by the shared connection pool.

    The pool manages connection lifecycle, so we do not close the client per request.
    """
    return get_redis_client()


def get_settings() -> Settings:
    return settings
