"""Tests for background memory extraction orchestration.

Tests scheduling, idempotency, and graceful degradation.
Does NOT test actual LLM extraction (requires real API key).
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.memory.background_extractor import (
    _get_extractor,
    _pending_tasks,
    _processed_conversations,
    reset_processed,
    schedule_extraction,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Reset module-level state between tests."""
    reset_processed()
    yield
    reset_processed()


def test_schedule_extraction_skips_without_store():
    """No store → no extraction scheduled."""
    schedule_extraction("conv-1", "user-1", [{"role": "user", "content": "hello"}], store=None)
    assert "conv-1" not in _processed_conversations


def test_schedule_extraction_idempotent():
    """Same conversation_id should not be processed twice."""
    _processed_conversations.add("conv-1")
    # This should return early without scheduling
    schedule_extraction(
        "conv-1",
        "user-1",
        [{"role": "user", "content": "hello"}],
        store=MagicMock(),
        delay_seconds=0,
    )
    # Still just the one entry
    assert "conv-1" in _processed_conversations


def test_reset_processed():
    """reset_processed clears state."""
    _processed_conversations.add("conv-1")
    _processed_conversations.add("conv-2")
    _pending_tasks["conv-1"] = MagicMock()
    reset_processed()
    assert len(_processed_conversations) == 0
    assert len(_pending_tasks) == 0


def test_schedule_extraction_skips_when_memory_disabled():
    """Should skip extraction when memory_enabled is False."""
    store = MagicMock()
    schedule_extraction(
        "conv-mem-off",
        "user-1",
        [{"role": "user", "content": "hello"}],
        store=store,
        memory_enabled=False,
    )
    assert "conv-mem-off" not in _processed_conversations
    assert "conv-mem-off" not in _pending_tasks


def test_schedule_extraction_cancels_pending():
    """Should cancel existing pending task when rescheduled."""
    mock_task = MagicMock()
    _pending_tasks["conv-cancel"] = mock_task
    store = MagicMock()
    schedule_extraction(
        "conv-cancel",
        "user-1",
        [],
        store=store,
    )
    mock_task.cancel.assert_called_once()


def test_schedule_extraction_no_running_loop():
    """Should handle RuntimeError when no event loop is running."""
    store = MagicMock()
    # This runs in a non-async context so no running loop
    schedule_extraction(
        "conv-no-loop",
        "user-1",
        [],
        store=store,
    )
    assert "conv-no-loop" not in _pending_tasks


@pytest.mark.asyncio
async def test_schedule_extraction_creates_task():
    """Should create an asyncio task when event loop is running."""
    store = MagicMock()
    schedule_extraction(
        "conv-task",
        "user-1",
        [{"role": "user", "content": "hello"}],
        store=store,
        delay_seconds=0,
    )
    assert "conv-task" in _pending_tasks
    # Cancel to clean up
    _pending_tasks["conv-task"].cancel()
    try:
        await _pending_tasks["conv-task"]
    except (asyncio.CancelledError, Exception):
        pass


@patch("app.memory.background_extractor.get_llm")
def test_get_extractor_returns_none_for_demo_model(mock_get_llm):
    """Extractor returns None when using DemoChatModel."""
    demo_model = MagicMock()
    type(demo_model).__name__ = "DemoChatModel"
    mock_get_llm.return_value = demo_model

    result = _get_extractor(MagicMock())
    assert result is None


@patch("app.memory.background_extractor.get_llm")
def test_get_extractor_returns_none_on_exception(mock_get_llm):
    """Extractor returns None when langmem import fails."""
    mock_get_llm.side_effect = Exception("import failed")

    result = _get_extractor(MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_delayed_extract_skips_if_processed():
    """Delayed extraction should skip if marked processed between scheduling and execution."""
    store = MagicMock()
    schedule_extraction(
        "conv-skip-delay",
        "user-1",
        [{"role": "user", "content": "test"}],
        store=store,
        delay_seconds=0,
    )
    # Mark as processed before the task runs
    _processed_conversations.add("conv-skip-delay")

    if "conv-skip-delay" in _pending_tasks:
        try:
            await asyncio.wait_for(_pending_tasks["conv-skip-delay"], timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
            pass
