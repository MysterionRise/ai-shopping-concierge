from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import HTTPException, Request
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


def verify_user_ownership(request: Request, user_id: str) -> None:
    """Validate that X-User-ID header matches the user_id in the request path/query.

    Lightweight ownership check for a demo project (no real auth).
    Raises HTTP 401 if the header is absent.
    Raises HTTP 403 if the header is present but does not match.
    """
    header_user_id = request.headers.get("x-user-id")
    if header_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-ID header required")
    if header_user_id != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
