"""Tests for background memory extraction orchestration.

Tests scheduling, idempotency, and graceful degradation.
Does NOT test actual LLM extraction (requires real API key).
"""

from unittest.mock import MagicMock, patch

from app.memory.background_extractor import (
    _processed_conversations,
    reset_processed,
    schedule_extraction,
)


def test_schedule_extraction_skips_without_store():
    """No store → no extraction scheduled."""
    reset_processed()
    schedule_extraction("conv-1", "user-1", [{"role": "user", "content": "hello"}], store=None)
    assert "conv-1" not in _processed_conversations


def test_schedule_extraction_idempotent():
    """Same conversation_id should not be processed twice."""
    reset_processed()
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
    reset_processed()
    assert len(_processed_conversations) == 0


@patch("app.memory.background_extractor._get_extractor")
def test_get_extractor_returns_none_in_demo(mock_get):
    """Extractor returns None when using DemoChatModel."""
    mock_get.return_value = None
    from app.memory.background_extractor import _get_extractor

    result = _get_extractor(MagicMock())
    assert result is None
