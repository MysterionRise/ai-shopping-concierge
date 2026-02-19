"""Shared fixtures for integration tests."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage


@pytest.fixture
def mock_llm(monkeypatch):
    """Patch LLM across all agent modules."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="Mock response"))

    def mock_get_llm(**kwargs):
        return mock

    monkeypatch.setattr("app.core.llm.get_llm", mock_get_llm)
    monkeypatch.setattr("app.agents.triage_router.get_llm", mock_get_llm)
    monkeypatch.setattr("app.agents.response_synth.get_llm", mock_get_llm)
    monkeypatch.setattr("app.agents.product_discovery.get_llm", mock_get_llm)
    monkeypatch.setattr("app.agents.safety_constraint.get_llm", mock_get_llm)
    return mock
