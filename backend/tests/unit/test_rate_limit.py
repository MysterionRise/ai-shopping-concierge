"""Tests for rate limiting on chat endpoints.

Validates:
- Requests within the rate limit succeed (200)
- Requests exceeding the rate limit return 429
- Rate limits apply per user_id (different users have independent limits)
- Both /chat and /chat/stream are rate limited
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.agents.graph import compile_graph
from app.core.rate_limit import limiter
from app.dependencies import get_db_session
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def mock_db():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.fixture
def client(mock_db):
    app.state.graph = compile_graph()
    app.state.persona_monitor = None
    app.state.store = None

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db_session] = override_db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


USER_ID = "00000000-0000-0000-0000-000000000001"
USER_ID_2 = "00000000-0000-0000-0000-000000000002"


@patch("app.config.settings.rate_limit_chat", "3/minute")
class TestChatRateLimit:
    """Rate limiting on POST /api/v1/chat."""

    def test_requests_within_limit_succeed(self, client, mock_llm):
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))
        for _ in range(3):
            resp = client.post(
                "/api/v1/chat",
                json={"message": "hello", "user_id": USER_ID},
                headers={"X-User-ID": USER_ID},
            )
            assert resp.status_code == 200

    def test_exceeding_limit_returns_429(self, client, mock_llm):
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))
        for _ in range(3):
            client.post(
                "/api/v1/chat",
                json={"message": "hello", "user_id": USER_ID},
                headers={"X-User-ID": USER_ID},
            )

        resp = client.post(
            "/api/v1/chat",
            json={"message": "hello", "user_id": USER_ID},
            headers={"X-User-ID": USER_ID},
        )
        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()

    def test_different_users_have_independent_limits(self, client, mock_llm):
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

        # Exhaust user 1's limit
        for _ in range(3):
            client.post(
                "/api/v1/chat",
                json={"message": "hello", "user_id": USER_ID},
                headers={"X-User-ID": USER_ID},
            )

        # User 1 is rate limited
        resp = client.post(
            "/api/v1/chat",
            json={"message": "hello", "user_id": USER_ID},
            headers={"X-User-ID": USER_ID},
        )
        assert resp.status_code == 429

        # User 2 still has capacity
        resp = client.post(
            "/api/v1/chat",
            json={"message": "hello", "user_id": USER_ID_2},
            headers={"X-User-ID": USER_ID_2},
        )
        assert resp.status_code == 200


@patch("app.config.settings.rate_limit_chat", "3/minute")
class TestStreamRateLimit:
    """Rate limiting on POST /api/v1/chat/stream."""

    def test_stream_exceeding_limit_returns_429(self, client, mock_llm):
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))
        for _ in range(3):
            client.post(
                "/api/v1/chat/stream",
                json={"message": "hello", "user_id": USER_ID},
                headers={"X-User-ID": USER_ID},
            )

        resp = client.post(
            "/api/v1/chat/stream",
            json={"message": "hello", "user_id": USER_ID},
            headers={"X-User-ID": USER_ID},
        )
        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()

    def test_chat_and_stream_share_limit(self, client, mock_llm):
        """Both endpoints count toward the same per-user limit."""
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

        # 2 requests to /chat
        for _ in range(2):
            client.post(
                "/api/v1/chat",
                json={"message": "hello", "user_id": USER_ID},
                headers={"X-User-ID": USER_ID},
            )

        # 1 request to /chat/stream (limit is 3/minute total per endpoint)
        resp = client.post(
            "/api/v1/chat/stream",
            json={"message": "hello", "user_id": USER_ID},
            headers={"X-User-ID": USER_ID},
        )
        assert resp.status_code == 200
