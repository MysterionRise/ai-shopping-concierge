"""Tests for user ownership validation (X-User-ID header check).

Verifies that:
- Matching X-User-ID header allows the request (200)
- Mismatching X-User-ID header blocks the request (403)
- Missing header returns 401 (header required)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langgraph.store.memory import InMemoryStore

from app.dependencies import get_db_session, verify_user_ownership
from app.main import app


@pytest.fixture
def mock_db():
    session = AsyncMock()
    return session


@pytest.fixture
def store():
    return InMemoryStore()


@pytest.fixture
def client(mock_db, store):
    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db_session] = override_db
    app.state.store = store
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()
    app.state.store = None


# ---------------------------------------------------------------------------
# Unit tests for verify_user_ownership
# ---------------------------------------------------------------------------


class TestVerifyUserOwnership:
    def test_no_header_raises_401(self):
        """Missing X-User-ID header should raise HTTPException with 401."""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.headers = {}
        with pytest.raises(HTTPException) as exc_info:
            verify_user_ownership(mock_request, "any-user-id")
        assert exc_info.value.status_code == 401
        assert "required" in exc_info.value.detail.lower()

    def test_matching_header_passes(self):
        """Matching header should not raise."""
        user_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_request.headers = {"x-user-id": user_id}
        verify_user_ownership(mock_request, user_id)

    def test_mismatching_header_raises_403(self):
        """Mismatching header should raise HTTPException with 403."""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.headers = {"x-user-id": "user-a"}
        with pytest.raises(HTTPException) as exc_info:
            verify_user_ownership(mock_request, "user-b")
        assert exc_info.value.status_code == 403
        assert "mismatch" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Conversations endpoint ownership tests
# ---------------------------------------------------------------------------


class TestConversationOwnership:
    def test_list_conversations_no_header(self, client, mock_db):
        """No header should return 401."""
        user_id = str(uuid.uuid4())

        resp = client.get(f"/api/v1/conversations?user_id={user_id}")
        assert resp.status_code == 401

    def test_list_conversations_matching_header(self, client, mock_db):
        """Matching header should allow request."""
        user_id = str(uuid.uuid4())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(
            f"/api/v1/conversations?user_id={user_id}",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200

    def test_list_conversations_mismatched_header(self, client, mock_db):
        """Mismatched header should return 403."""
        user_id = str(uuid.uuid4())
        other_id = str(uuid.uuid4())

        resp = client.get(
            f"/api/v1/conversations?user_id={user_id}",
            headers={"X-User-ID": other_id},
        )
        assert resp.status_code == 403

    def test_get_messages_mismatched_header(self, client, mock_db):
        """Mismatched header on messages endpoint should return 403."""
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        resp = client.get(
            f"/api/v1/conversations/{conv_id}/messages?user_id={user_id}",
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403

    def test_get_messages_matching_header(self, client, mock_db):
        """Matching header on messages endpoint should allow request."""
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        conv = MagicMock()
        conv.id = conv_id
        conv.user_id = user_id

        conv_result = MagicMock()
        conv_result.scalar_one_or_none.return_value = conv
        msg_result = MagicMock()
        msg_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[conv_result, msg_result])

        resp = client.get(
            f"/api/v1/conversations/{conv_id}/messages?user_id={user_id}",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Memory endpoint ownership tests
# ---------------------------------------------------------------------------


class TestMemoryOwnership:
    def test_get_memories_no_header(self, client):
        """No header should return 401."""
        user_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/users/{user_id}/memory")
        assert resp.status_code == 401

    def test_get_memories_matching_header(self, client):
        """Matching header should allow request."""
        user_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/users/{user_id}/memory",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200

    def test_get_memories_mismatched_header(self, client):
        """Mismatched header should return 403."""
        user_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/users/{user_id}/memory",
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403

    def test_delete_memory_mismatched_header(self, client):
        """Mismatched header on delete should return 403."""
        user_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/users/{user_id}/memory/some-id",
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403

    def test_get_constraints_mismatched_header(self, client):
        """Mismatched header on constraints should return 403."""
        user_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/users/{user_id}/memory/constraints",
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403

    @patch("app.api.routes.memory.add_constraint")
    def test_add_constraint_mismatched_header(self, mock_add, client):
        """Mismatched header on add constraint should return 403."""
        user_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/users/{user_id}/memory/constraints",
            json={"constraint": "paraben", "is_hard": True},
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403

    @patch("app.api.routes.memory.add_constraint")
    def test_add_constraint_matching_header(self, mock_add, client, store):
        """Matching header on add constraint should allow request."""
        mock_add.return_value = None
        user_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/users/{user_id}/memory/constraints",
            json={"constraint": "paraben", "is_hard": True},
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Chat endpoint ownership tests
# ---------------------------------------------------------------------------


class TestChatOwnership:
    @pytest.fixture(autouse=True)
    def setup_graph(self):
        """Provide a mock graph on app.state and disable rate limiter for tests."""
        from app.agents.graph import compile_graph
        from app.core.rate_limit import limiter

        app.state.graph = compile_graph()
        limiter.enabled = False
        yield
        limiter.enabled = True

    def test_chat_mismatched_header(self, client):
        """Mismatched header on /chat should return 403."""
        user_id = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/chat",
            json={"message": "hello", "user_id": user_id},
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403

    def test_chat_no_header(self, client, mock_db):
        """No header on /chat should return 401."""
        user_id = str(uuid.uuid4())

        resp = client.post(
            "/api/v1/chat",
            json={"message": "hello", "user_id": user_id},
        )
        assert resp.status_code == 401

    def test_chat_stream_mismatched_header(self, client):
        """Mismatched header on /chat/stream should return 403."""
        user_id = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/chat/stream",
            json={"message": "hello", "user_id": user_id},
            headers={"X-User-ID": str(uuid.uuid4())},
        )
        assert resp.status_code == 403
