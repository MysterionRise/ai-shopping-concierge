import uuid

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.memory.constraint_store import add_constraint
from app.memory.langmem_config import constraints_ns, user_facts_ns

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


@router.get("", response_model=list[MemoryResponse])
async def get_user_memories(user_id: str, request: Request):
    """Get all memories for a user from the LangMem store."""
    store = getattr(request.app.state, "store", None)
    if store is None:
        return []

    memories = []
    # Search user_facts namespace
    try:
        facts = await store.asearch(user_facts_ns(user_id), limit=50)
        for item in facts:
            memories.append(
                MemoryResponse(
                    id=item.key,
                    content=item.value.get("content", str(item.value)),
                    category=item.value.get("category", "user_fact"),
                    metadata={k: v for k, v in item.value.items() if k != "content"},
                    created_at=item.value.get("created_at", ""),
                )
            )
    except Exception as e:
        logger.warning("Failed to load user facts", error=str(e))

    # Search constraints namespace
    try:
        constraint_items = await store.asearch(constraints_ns(user_id), limit=50)
        for item in constraint_items:
            memories.append(
                MemoryResponse(
                    id=item.key,
                    content=item.value.get("content", str(item.value)),
                    category="constraints",
                    metadata={k: v for k, v in item.value.items() if k != "content"},
                    created_at=item.value.get("created_at", ""),
                )
            )
    except Exception as e:
        logger.warning("Failed to load constraints", error=str(e))

    return memories


@router.delete("/{memory_id}")
async def delete_memory(user_id: str, memory_id: str, request: Request):
    """Delete a memory from the LangMem store."""
    store = getattr(request.app.state, "store", None)
    if store is None:
        return {"status": "not_found"}

    # Try deleting from both namespaces
    for ns_fn in (user_facts_ns, constraints_ns):
        try:
            item = await store.aget(ns_fn(user_id), memory_id)
            if item is not None:
                await store.adelete(ns_fn(user_id), memory_id)
                return {"status": "deleted"}
        except Exception as e:
            logger.warning("Failed to delete memory", error=str(e))

    return {"status": "not_found"}


@router.get("/constraints", response_model=list[MemoryResponse])
async def get_constraints(user_id: str, request: Request):
    """Get all constraints from the LangMem store."""
    store = getattr(request.app.state, "store", None)
    if store is None:
        return []

    try:
        items = await store.asearch(constraints_ns(user_id), limit=50)
        return [
            MemoryResponse(
                id=item.key,
                content=item.value.get("content", str(item.value)),
                category="constraints",
                metadata={k: v for k, v in item.value.items() if k != "content"},
                created_at=item.value.get("created_at", ""),
            )
            for item in items
        ]
    except Exception as e:
        logger.warning("Failed to load constraints", error=str(e))
        return []


@router.post("/constraints")
async def add_user_constraint(
    user_id: str,
    data: ConstraintCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Add a constraint to the LangMem store and Postgres."""
    memory_id = f"constraint_{uuid.uuid4().hex[:8]}"
    store = getattr(request.app.state, "store", None)

    if store is not None:
        ns = constraints_ns(user_id) if data.is_hard else user_facts_ns(user_id)
        await store.aput(
            ns,
            memory_id,
            {
                "ingredient": data.constraint,
                "severity": "absolute" if data.is_hard else "preference",
                "source": "user_api",
                "content": data.constraint,
            },
        )

    # Also persist to Postgres User.allergies/preferences for safety agent
    await add_constraint(db, user_id, data.constraint, is_hard=data.is_hard)
    return {"id": memory_id, "status": "created"}
