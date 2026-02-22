"""Smoke tests for the conversations API routes.

Tests list conversations and get messages endpoints with mocked database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db_session
from app.main import app


def _make_mock_conversation(**overrides):
    """Create a mock Conversation ORM object."""
    conv = MagicMock()
    conv.id = overrides.get("id", uuid.uuid4())
    conv.user_id = overrides.get("user_id", uuid.uuid4())
    conv.langgraph_thread_id = overrides.get("langgraph_thread_id", str(uuid.uuid4()))
    conv.title = overrides.get("title", "Test conversation")
    conv.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    return conv


def _make_mock_message(**overrides):
    """Create a mock Message ORM object."""
    msg = MagicMock()
    msg.id = overrides.get("id", uuid.uuid4())
    msg.conversation_id = overrides.get("conversation_id", uuid.uuid4())
    msg.role = overrides.get("role", "user")
    msg.content = overrides.get("content", "Hello!")
    msg.agent_name = overrides.get("agent_name", None)
    msg.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    return msg


@pytest.fixture
def mock_db():
    session = AsyncMock()
    return session


@pytest.fixture
def client(mock_db):
    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db_session] = override_db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


class TestListConversations:
    def test_list_conversations_returns_list(self, client, mock_db):
        """GET /api/v1/conversations?user_id= should return conversations."""
        user_id = str(uuid.uuid4())
        conv1 = _make_mock_conversation(user_id=user_id, title="Chat 1")
        conv2 = _make_mock_conversation(user_id=user_id, title="Chat 2")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [conv1, conv2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/conversations?user_id={user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "Chat 1"
        assert data[1]["title"] == "Chat 2"

    def test_list_conversations_empty(self, client, mock_db):
        """Should return empty list when user has no conversations."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/conversations?user_id={uuid.uuid4()}")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_conversations_response_shape(self, client, mock_db):
        """Each conversation should have required fields."""
        conv = _make_mock_conversation()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [conv]
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/conversations?user_id={uuid.uuid4()}")
        data = resp.json()
        item = data[0]
        assert "id" in item
        assert "user_id" in item
        assert "langgraph_thread_id" in item
        assert "title" in item
        assert "created_at" in item

    def test_list_conversations_requires_user_id(self, client):
        """Missing user_id query param should return 422."""
        resp = client.get("/api/v1/conversations")
        assert resp.status_code == 422


class TestGetMessages:
    def test_get_messages_found(self, client, mock_db):
        """GET /api/v1/conversations/{id}/messages should return messages."""
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())
        conv = _make_mock_conversation(id=conv_id, user_id=user_id)

        msg1 = _make_mock_message(role="user", content="Hi there")
        msg2 = _make_mock_message(role="assistant", content="Hello!", agent_name="general_chat")

        # First execute: find conversation
        conv_result = MagicMock()
        conv_result.scalar_one_or_none.return_value = conv
        # Second execute: get messages
        msg_result = MagicMock()
        msg_result.scalars.return_value.all.return_value = [msg1, msg2]

        mock_db.execute = AsyncMock(side_effect=[conv_result, msg_result])

        resp = client.get(f"/api/v1/conversations/{conv_id}/messages?user_id={user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "Hi there"
        assert data[1]["role"] == "assistant"
        assert data[1]["agent_name"] == "general_chat"

    def test_get_messages_conversation_not_found(self, client, mock_db):
        """Should return 404 when conversation doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/conversations/{uuid.uuid4()}/messages?user_id={uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Conversation not found"

    def test_get_messages_response_shape(self, client, mock_db):
        """Each message should have required fields."""
        conv = _make_mock_conversation()
        msg = _make_mock_message(content="Test message")

        conv_result = MagicMock()
        conv_result.scalar_one_or_none.return_value = conv
        msg_result = MagicMock()
        msg_result.scalars.return_value.all.return_value = [msg]
        mock_db.execute = AsyncMock(side_effect=[conv_result, msg_result])

        resp = client.get(f"/api/v1/conversations/{conv.id}/messages?user_id={conv.user_id}")
        data = resp.json()
        item = data[0]
        assert "id" in item
        assert "role" in item
        assert "content" in item
        assert "agent_name" in item
        assert "created_at" in item
