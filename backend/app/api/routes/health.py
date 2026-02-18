import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, get_redis

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db_session),
    redis=Depends(get_redis),
):
    checks = {"status": "healthy", "postgres": "ok", "redis": "ok"}

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Postgres health check failed", error=str(e))
        checks["postgres"] = "error"
        checks["status"] = "degraded"

    try:
        await redis.ping()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        checks["redis"] = "error"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)
