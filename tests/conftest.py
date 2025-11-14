"""Pytest configuration and fixtures."""

import os
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_anthropic_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Anthropic API key for all tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("USE_MOCK_DATA", "true")


@pytest.fixture
def mock_claude_response() -> Generator[AsyncMock, None, None]:
    """Mock Claude API response."""

    class MockBlock:
        def __init__(self, text: str):
            self.text = text

    class MockUsage:
        input_tokens: int = 100
        output_tokens: int = 50

        def model_dump(self) -> dict:
            return {"input_tokens": 100, "output_tokens": 50}

    class MockResponse:
        def __init__(self, text: str):
            self.content = [MockBlock(text)]
            self.usage = MockUsage()

    mock_create = AsyncMock()

    with patch("anthropic.Anthropic") as mock_client:
        mock_instance = MagicMock()
        mock_instance.messages.create = mock_create
        mock_client.return_value = mock_instance

        yield mock_create


@pytest.fixture
def mock_claude_json_response() -> str:
    """Get a mock JSON response from Claude."""
    return """
    {
        "ready": true,
        "product_category": "running shoes",
        "budget": {"min": 0, "max": 150},
        "must_have_features": ["cushioning", "breathable"],
        "nice_to_have_features": ["lightweight"],
        "constraints": ["under $150"],
        "use_case": "daily running and training",
        "confidence_level": "high"
    }
    """
