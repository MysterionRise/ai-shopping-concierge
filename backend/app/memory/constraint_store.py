import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = structlog.get_logger()


def get_user_constraints(user: User) -> tuple[list[str], list[str]]:
    """Extract hard constraints and soft preferences from a User object.

    Returns (hard_constraints, soft_preferences) tuple.
    """
    hard_constraints: list[str] = []
    if user.allergies and isinstance(user.allergies, list):
        hard_constraints = list(user.allergies)

    soft_preferences: list[str] = []
    if user.preferences:
        prefs = user.preferences
        if isinstance(prefs, dict):
            soft_preferences = [f"{k}: {v}" for k, v in prefs.items()]
        elif isinstance(prefs, list):
            soft_preferences = list(prefs)

    return hard_constraints, soft_preferences


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
