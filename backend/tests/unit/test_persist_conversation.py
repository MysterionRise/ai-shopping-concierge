"""Tests for _persist_conversation in chat route.

Validates:
- Conversation lookup by DB id (primary) and langgraph_thread_id (fallback)
- New conversation creation with correct langgraph_thread_id
- Empty/whitespace assistant response is not persisted
- Messages are correctly associated with the conversation
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.routes.chat import _persist_conversation
from app.models.conversation import Conversation


def _make_db():
    """Create a mock async DB session with sync add() and async execute/flush/commit."""
    db = AsyncMock()
    # db.add is synchronous in SQLAlchemy, so use MagicMock to avoid warnings
    db.add = MagicMock()
    return db


def _make_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    return user


def _make_conversation(user_id, thread_id="thread-abc"):
    conv = MagicMock(spec=Conversation)
    conv.id = uuid.uuid4()
    conv.user_id = user_id
    conv.langgraph_thread_id = thread_id
    return conv


@pytest.mark.asyncio
async def test_persist_creates_new_conversation():
    """When no matching conversation exists, a new one is created."""
    db = _make_db()
    user = _make_user()
    conv_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    # Both lookups return None (no existing conversation)
    result_none = MagicMock()
    result_none.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_none)

    persisted_id = await _persist_conversation(
        db, user, conv_id, thread_id, "Hello", "Hi there!", intent="general_chat"
    )

    assert persisted_id is not None
    # Should have called db.add for conversation + 2 messages = 3 calls
    assert db.add.call_count == 3
    assert db.flush.called
    assert db.commit.called

    # Check the new conversation was created with thread_id as langgraph_thread_id
    new_conv = db.add.call_args_list[0][0][0]
    assert isinstance(new_conv, Conversation)
    assert new_conv.langgraph_thread_id == thread_id
    assert new_conv.user_id == user.id


@pytest.mark.asyncio
async def test_persist_finds_existing_by_db_id():
    """When conversation exists by DB id, it is reused (no new creation)."""
    db = _make_db()
    user = _make_user()
    existing_conv = _make_conversation(user.id)
    conv_id = str(existing_conv.id)
    thread_id = str(uuid.uuid4())

    # First lookup (by DB id) returns the existing conversation
    result_found = MagicMock()
    result_found.scalar_one_or_none.return_value = existing_conv
    db.execute = AsyncMock(return_value=result_found)

    result = await _persist_conversation(db, user, conv_id, thread_id, "Hello", "Hi there!")

    assert result == str(existing_conv.id)
    # Should add 2 messages, no new conversation
    assert db.add.call_count == 2
    assert not db.flush.called
    assert db.commit.called


@pytest.mark.asyncio
async def test_persist_falls_back_to_thread_id_lookup():
    """When DB id lookup fails, falls back to langgraph_thread_id."""
    db = _make_db()
    user = _make_user()
    thread_id = "thread-xyz"
    existing_conv = _make_conversation(user.id, thread_id=thread_id)
    conv_id = str(uuid.uuid4())  # A different id that won't match

    # First call (by DB id) returns None, second call (by thread_id) returns conv
    result_none = MagicMock()
    result_none.scalar_one_or_none.return_value = None
    result_found = MagicMock()
    result_found.scalar_one_or_none.return_value = existing_conv
    db.execute = AsyncMock(side_effect=[result_none, result_found])

    result = await _persist_conversation(db, user, conv_id, thread_id, "Hello", "Hi there!")

    assert result == str(existing_conv.id)
    # 2 execute calls (DB id + thread_id), 2 message adds, no flush
    assert db.execute.call_count == 2
    assert db.add.call_count == 2
    assert not db.flush.called


@pytest.mark.asyncio
async def test_persist_skips_empty_response():
    """Empty or whitespace-only assistant responses should not be persisted."""
    db = _make_db()
    user = _make_user()

    for empty_response in ["", "   ", "\n\t"]:
        result = await _persist_conversation(
            db, user, "conv-1", "thread-1", "Hello", empty_response
        )
        assert result is None

    # DB should never have been called
    assert not db.execute.called
    assert not db.commit.called


@pytest.mark.asyncio
async def test_persist_returns_none_without_user():
    """When user is None, no persistence happens."""
    db = _make_db()

    result = await _persist_conversation(db, None, "conv-1", "thread-1", "Hello", "Hi there!")

    assert result is None
    assert not db.execute.called
    assert not db.commit.called


@pytest.mark.asyncio
async def test_persist_handles_db_error_gracefully():
    """DB errors should be caught and return None."""
    db = _make_db()
    user = _make_user()
    db.execute = AsyncMock(side_effect=Exception("DB connection lost"))

    result = await _persist_conversation(db, user, "conv-1", "thread-1", "Hello", "Hi there!")

    assert result is None


@pytest.mark.asyncio
async def test_persist_handles_integrity_error(caplog):
    """IntegrityError should be caught, logged as ERROR, and return None."""
    from sqlalchemy.exc import IntegrityError

    db = _make_db()
    user = _make_user()
    db.execute = AsyncMock(
        side_effect=IntegrityError("duplicate key", params=None, orig=Exception("dup"))
    )

    result = await _persist_conversation(db, user, "conv-1", "thread-1", "Hello", "Hi there!")

    assert result is None


@pytest.mark.asyncio
async def test_persist_handles_operational_error():
    """OperationalError should be caught and return None."""
    from sqlalchemy.exc import OperationalError

    db = _make_db()
    user = _make_user()
    db.execute = AsyncMock(
        side_effect=OperationalError("connection refused", params=None, orig=Exception("conn"))
    )

    result = await _persist_conversation(db, user, "conv-1", "thread-1", "Hello", "Hi there!")

    assert result is None
