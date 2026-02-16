import json
from unittest.mock import AsyncMock

import pytest

from app.memory.memory_manager import MemoryManager


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=0)
    redis.lrange = AsyncMock(return_value=[])

    async def mock_scan_iter(match=None):
        return
        yield  # noqa: make it an async generator

    redis.scan_iter = mock_scan_iter
    return redis


@pytest.fixture
def manager(mock_redis):
    return MemoryManager(mock_redis)


async def test_store_memory(manager, mock_redis):
    memory_id = await manager.store_memory("user-1", "semantic", "Has oily skin")
    assert memory_id is not None
    mock_redis.set.assert_called_once()


async def test_store_memory_with_metadata(manager, mock_redis):
    await manager.store_memory(
        "user-1",
        "constraints",
        "Allergic to parabens",
        metadata={"source": "conversation"},
    )
    call_args = mock_redis.set.call_args
    stored = json.loads(call_args[0][1])
    assert stored["category"] == "constraints"
    assert stored["metadata"]["source"] == "conversation"


async def test_retrieve_relevant_empty(manager):
    result = await manager.retrieve_relevant("user-1", "moisturizer")
    assert result == []


async def test_delete_memory_not_found(manager, mock_redis):
    result = await manager.delete_memory("user-1", "nonexistent-id")
    assert result is False


async def test_get_all_memories_empty(manager):
    result = await manager.get_all_memories("user-1")
    assert result == []


async def test_learn_from_conversation_allergy(manager, mock_redis):
    messages = [
        {"role": "user", "content": "I'm allergic to sulfates in my shampoo"},
    ]
    await manager.learn_from_conversation("user-1", messages)
    assert mock_redis.set.call_count >= 1
