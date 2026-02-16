import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = structlog.get_logger()


async def get_hard_constraints(db: AsyncSession, user_id: str) -> list[str]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.allergies:
        return []
    return user.allergies if isinstance(user.allergies, list) else []


async def get_soft_preferences(db: AsyncSession, user_id: str) -> list[str]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.preferences:
        return []
    prefs = user.preferences
    if isinstance(prefs, dict):
        return [f"{k}: {v}" for k, v in prefs.items()]
    return prefs if isinstance(prefs, list) else []


async def add_constraint(db: AsyncSession, user_id: str, constraint: str, is_hard: bool = True):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning("User not found for constraint", user_id=user_id)
        return

    if is_hard:
        allergies: list[str] = list(user.allergies or [])
        if constraint not in allergies:
            allergies.append(constraint)
            user.allergies = allergies  # type: ignore[assignment]
    else:
        preferences = user.preferences or {}
        if isinstance(preferences, dict):
            preferences[constraint] = True
            user.preferences = preferences

    await db.commit()
    logger.info("Constraint added", user_id=user_id, constraint=constraint, is_hard=is_hard)
