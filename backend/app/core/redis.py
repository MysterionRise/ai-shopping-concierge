import redis.asyncio as aioredis

from app.config import settings

# Module-level pool kept for backward compatibility (used by get_redis_client
# before the app lifespan initializes app state).  The lifespan manager in
# main.py stores this same pool on app.state and closes it on shutdown.
redis_pool = aioredis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis_client() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=redis_pool)
