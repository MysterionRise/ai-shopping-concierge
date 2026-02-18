import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, get_redis
from app.memory.constraint_store import add_constraint
from app.memory.memory_manager import MemoryManager

logger = structlog.get_logger()

router = APIRouter(prefix="/users/{user_id}/memory", tags=["memory"])


class MemoryResponse(BaseModel):
    id: str
    content: str
    category: str
    metadata: dict
    created_at: str


class ConstraintCreate(BaseModel):
    constraint: str
    is_hard: bool = True


async def get_memory_manager(redis=Depends(get_redis)) -> MemoryManager:
    return MemoryManager(redis)


@router.get("", response_model=list[MemoryResponse])
async def get_user_memories(
    user_id: str,
    manager: MemoryManager = Depends(get_memory_manager),
):
    memories = await manager.get_all_memories(user_id)
    return [
        MemoryResponse(
            id=m.get("id", ""),
            content=m.get("content", ""),
            category=m.get("category", ""),
            metadata=m.get("metadata", {}),
            created_at=m.get("created_at", ""),
        )
        for m in memories
    ]


@router.delete("/{memory_id}")
async def delete_memory(
    user_id: str,
    memory_id: str,
    manager: MemoryManager = Depends(get_memory_manager),
):
    deleted = await manager.delete_memory(user_id, memory_id)
    if not deleted:
        return {"status": "not_found"}
    return {"status": "deleted"}


@router.get("/constraints", response_model=list[MemoryResponse])
async def get_constraints(
    user_id: str,
    manager: MemoryManager = Depends(get_memory_manager),
):
    constraints = await manager.get_all_constraints(user_id)
    return [
        MemoryResponse(
            id=m.get("id", ""),
            content=m.get("content", ""),
            category=m.get("category", "constraints"),
            metadata=m.get("metadata", {}),
            created_at=m.get("created_at", ""),
        )
        for m in constraints
    ]


@router.post("/constraints")
async def add_user_constraint(
    user_id: str,
    data: ConstraintCreate,
    manager: MemoryManager = Depends(get_memory_manager),
    db: AsyncSession = Depends(get_db_session),
):
    category = "constraints" if data.is_hard else "preferences"
    memory_id = await manager.store_memory(
        user_id,
        category,
        data.constraint,
        metadata={"type": "user_defined", "is_hard": data.is_hard},
    )
    # Also persist to Postgres User.allergies/preferences so the safety agent can use it
    await add_constraint(db, user_id, data.constraint, is_hard=data.is_hard)
    return {"id": memory_id, "status": "created"}
