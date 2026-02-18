"""Memory manager — abstraction layer over LangMem/direct storage.

All LangMem SDK calls are wrapped here. If LangMem breaks, only this file changes.
Fallback: direct Postgres queries via SQLAlchemy.
"""

import json
import uuid
from datetime import UTC, datetime

import redis.asyncio as aioredis
import structlog

from app.memory.langmem_config import MEMORY_CATEGORIES, get_memory_namespace

logger = structlog.get_logger()

REDIS_MEMORY_PREFIX = "memory:"


class MemoryManager:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def store_memory(
        self,
        user_id: str,
        category: str,
        content: str,
        metadata: dict | None = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        namespace = get_memory_namespace(user_id, category)
        key = f"{REDIS_MEMORY_PREFIX}{':'.join(namespace)}:{memory_id}"

        memory = {
            "id": memory_id,
            "content": content,
            "category": category,
            "metadata": metadata or {},
            "created_at": datetime.now(UTC).isoformat(),
        }

        try:
            await self.redis.set(key, json.dumps(memory))
            logger.info("Memory stored", user_id=user_id, category=category)
        except Exception as e:
            logger.error("Failed to store memory", error=str(e))

        return memory_id

    async def retrieve_relevant(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        memories = []
        for category in MEMORY_CATEGORIES:
            namespace = get_memory_namespace(user_id, category)
            pattern = f"{REDIS_MEMORY_PREFIX}{':'.join(namespace)}:*"
            try:
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                for key in keys[:limit]:
                    data = await self.redis.get(key)
                    if data:
                        memories.append(json.loads(data))
            except Exception as e:
                logger.error("Failed to retrieve memories", error=str(e))

        # Simple relevance: keyword overlap (will be replaced with vector search)
        query_words = set(query.lower().split())
        scored = []
        for m in memories:
            content_words = set(m.get("content", "").lower().split())
            overlap = len(query_words & content_words)
            scored.append((overlap, m))
        scored.sort(key=lambda x: x[0], reverse=True)

        return [m for _, m in scored[:limit]]

    async def get_all_constraints(self, user_id: str) -> list[dict]:
        namespace = get_memory_namespace(user_id, "constraints")
        pattern = f"{REDIS_MEMORY_PREFIX}{':'.join(namespace)}:*"
        constraints = []
        try:
            async for key in self.redis.scan_iter(match=pattern):
                data = await self.redis.get(key)
                if data:
                    constraints.append(json.loads(data))
        except Exception as e:
            logger.error("Failed to get constraints", error=str(e))
        return constraints

    async def get_all_memories(self, user_id: str) -> list[dict]:
        all_memories = []
        for category in MEMORY_CATEGORIES:
            namespace = get_memory_namespace(user_id, category)
            pattern = f"{REDIS_MEMORY_PREFIX}{':'.join(namespace)}:*"
            try:
                async for key in self.redis.scan_iter(match=pattern):
                    data = await self.redis.get(key)
                    if data:
                        all_memories.append(json.loads(data))
            except Exception as e:
                logger.error("Failed to get memories", error=str(e))
        return all_memories

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        for category in MEMORY_CATEGORIES:
            namespace = get_memory_namespace(user_id, category)
            key = f"{REDIS_MEMORY_PREFIX}{':'.join(namespace)}:{memory_id}"
            try:
                deleted = await self.redis.delete(key)
                if deleted:
                    return True
            except Exception as e:
                logger.error("Failed to delete memory", error=str(e))
        return False

    # learn_from_conversation() removed — replaced by background_extractor.py (2C.3)
