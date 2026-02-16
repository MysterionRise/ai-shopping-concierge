from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_llm(monkeypatch):
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


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    return session


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()
    return redis
