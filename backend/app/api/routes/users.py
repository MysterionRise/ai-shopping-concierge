import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    skin_type: str | None = None
    skin_concerns: list[str] = []
    allergies: list[str] = []
    preferences: dict = {}
    memory_enabled: bool = True


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    skin_type: str | None = None
    skin_concerns: list[str] | None = None
    allergies: list[str] | None = None
    preferences: dict | None = None
    memory_enabled: bool | None = None


class UserResponse(BaseModel):
    id: str
    display_name: str
    skin_type: str | None
    skin_concerns: list
    allergies: list
    preferences: dict
    memory_enabled: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).order_by(User.display_name))
    users = result.scalars().all()
    return [
        UserResponse(
            id=str(u.id),
            display_name=u.display_name,
            skin_type=u.skin_type,
            skin_concerns=list(u.skin_concerns or []),
            allergies=list(u.allergies or []),
            preferences=u.preferences or {},
            memory_enabled=u.memory_enabled,
        )
        for u in users
    ]


@router.post("", response_model=UserResponse)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    user = User(
        id=uuid.uuid4(),
        display_name=data.display_name,
        skin_type=data.skin_type,
        skin_concerns=data.skin_concerns,
        allergies=data.allergies,
        preferences=data.preferences,
        memory_enabled=data.memory_enabled,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        display_name=user.display_name,
        skin_type=user.skin_type,
        skin_concerns=list(user.skin_concerns or []),
        allergies=list(user.allergies or []),
        preferences=user.preferences or {},
        memory_enabled=user.memory_enabled,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        display_name=user.display_name,
        skin_type=user.skin_type,
        skin_concerns=list(user.skin_concerns or []),
        allergies=list(user.allergies or []),
        preferences=user.preferences or {},
        memory_enabled=user.memory_enabled,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.display_name is not None:
        user.display_name = data.display_name
    if data.skin_type is not None:
        user.skin_type = data.skin_type
    if data.skin_concerns is not None:
        user.skin_concerns = data.skin_concerns  # type: ignore[assignment]
    if data.allergies is not None:
        user.allergies = data.allergies  # type: ignore[assignment]
    if data.preferences is not None:
        user.preferences = data.preferences
    if data.memory_enabled is not None:
        user.memory_enabled = data.memory_enabled

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        display_name=user.display_name,
        skin_type=user.skin_type,
        skin_concerns=list(user.skin_concerns or []),
        allergies=list(user.allergies or []),
        preferences=user.preferences or {},
        memory_enabled=user.memory_enabled,
    )
