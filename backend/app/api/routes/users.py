import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    display_name: str
    skin_type: str | None = None
    skin_concerns: list[str] = []
    allergies: list[str] = []
    preferences: dict = {}


class UserUpdate(BaseModel):
    display_name: str | None = None
    skin_type: str | None = None
    skin_concerns: list[str] | None = None
    allergies: list[str] | None = None
    preferences: dict | None = None


class UserResponse(BaseModel):
    id: str
    display_name: str
    skin_type: str | None
    skin_concerns: list
    allergies: list
    preferences: dict

    model_config = {"from_attributes": True}


@router.post("", response_model=UserResponse)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    user = User(
        id=uuid.uuid4(),
        display_name=data.display_name,
        skin_type=data.skin_type,
        skin_concerns=data.skin_concerns,
        allergies=data.allergies,
        preferences=data.preferences,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        display_name=user.display_name,
        skin_type=user.skin_type,
        skin_concerns=user.skin_concerns or [],
        allergies=user.allergies or [],
        preferences=user.preferences or {},
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
        skin_concerns=user.skin_concerns or [],
        allergies=user.allergies or [],
        preferences=user.preferences or {},
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
        user.skin_concerns = data.skin_concerns
    if data.allergies is not None:
        user.allergies = data.allergies
    if data.preferences is not None:
        user.preferences = data.preferences

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        display_name=user.display_name,
        skin_type=user.skin_type,
        skin_concerns=user.skin_concerns or [],
        allergies=user.allergies or [],
        preferences=user.preferences or {},
    )
