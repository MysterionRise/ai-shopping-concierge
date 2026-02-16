import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.redis import get_redis_client
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


def get_memory_manager() -> MemoryManager:
    return MemoryManager(get_redis_client())


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
async def add_constraint(
    user_id: str,
    data: ConstraintCreate,
    manager: MemoryManager = Depends(get_memory_manager),
):
    category = "constraints" if data.is_hard else "preferences"
    memory_id = await manager.store_memory(
        user_id,
        category,
        data.constraint,
        metadata={"type": "user_defined", "is_hard": data.is_hard},
    )
    return {"id": memory_id, "status": "created"}
