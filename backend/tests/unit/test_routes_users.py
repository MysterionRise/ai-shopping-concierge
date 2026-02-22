"""Smoke tests for the users API routes.

Tests create, get, and update user endpoints with mocked database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db_session
from app.main import app


def _make_mock_user(**overrides):
    """Create a mock User ORM object."""
    user = MagicMock()
    user.id = overrides.get("id", uuid.uuid4())
    user.display_name = overrides.get("display_name", "Test User")
    user.skin_type = overrides.get("skin_type", "oily")
    user.skin_concerns = overrides.get("skin_concerns", ["acne"])
    user.allergies = overrides.get("allergies", ["paraben"])
    user.preferences = overrides.get("preferences", {"fragrance_free": True})
    user.memory_enabled = overrides.get("memory_enabled", True)
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def client(mock_db):
    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db_session] = override_db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


class TestCreateUser:
    def test_create_user_returns_expected_shape(self, client, mock_db):
        """POST /api/v1/users should return user with all fields."""
        user_id = uuid.uuid4()

        async def fake_refresh(obj):
            obj.id = user_id

        mock_db.refresh = AsyncMock(side_effect=fake_refresh)

        resp = client.post(
            "/api/v1/users",
            json={
                "display_name": "Alice",
                "skin_type": "dry",
                "skin_concerns": ["redness"],
                "allergies": ["sulfate"],
                "preferences": {"vegan": True},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Alice"
        assert data["skin_type"] == "dry"
        assert data["skin_concerns"] == ["redness"]
        assert data["allergies"] == ["sulfate"]
        assert data["preferences"] == {"vegan": True}
        assert data["memory_enabled"] is True
        assert "id" in data

    def test_create_user_minimal_fields(self, client, mock_db):
        """Only display_name is required."""
        user_id = uuid.uuid4()

        async def fake_refresh(obj):
            obj.id = user_id

        mock_db.refresh = AsyncMock(side_effect=fake_refresh)

        resp = client.post(
            "/api/v1/users",
            json={"display_name": "Bob"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Bob"
        assert data["skin_concerns"] == []
        assert data["allergies"] == []

    def test_create_user_missing_display_name(self, client):
        """Missing display_name should return 422."""
        resp = client.post("/api/v1/users", json={"skin_type": "oily"})
        assert resp.status_code == 422


class TestGetUser:
    def test_get_user_found(self, client, mock_db):
        """GET /api/v1/users/{id} should return user when found."""
        user = _make_mock_user(display_name="Carol")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/users/{user.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Carol"
        assert data["skin_type"] == "oily"
        assert data["allergies"] == ["paraben"]
        assert data["memory_enabled"] is True

    def test_get_user_not_found(self, client, mock_db):
        """GET /api/v1/users/{id} should return 404 when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/users/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "User not found"


class TestUpdateUser:
    def test_update_user_partial(self, client, mock_db):
        """PATCH /api/v1/users/{id} should update only provided fields."""
        user = _make_mock_user(display_name="Dave", skin_type="oily")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        resp = client.patch(
            f"/api/v1/users/{user.id}",
            json={"skin_type": "dry"},
        )
        assert resp.status_code == 200
        # The mock user's skin_type should have been set
        assert user.skin_type == "dry"

    def test_update_user_not_found(self, client, mock_db):
        """PATCH /api/v1/users/{id} should return 404 when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.patch(
            f"/api/v1/users/{uuid.uuid4()}",
            json={"display_name": "New Name"},
        )
        assert resp.status_code == 404

    def test_update_user_allergies(self, client, mock_db):
        """PATCH should update allergies list."""
        user = _make_mock_user(allergies=["paraben"])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        resp = client.patch(
            f"/api/v1/users/{user.id}",
            json={"allergies": ["paraben", "sulfate"]},
        )
        assert resp.status_code == 200
        assert user.allergies == ["paraben", "sulfate"]

    def test_update_user_memory_enabled(self, client, mock_db):
        """PATCH should update memory_enabled flag."""
        user = _make_mock_user(memory_enabled=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        resp = client.patch(
            f"/api/v1/users/{user.id}",
            json={"memory_enabled": False},
        )
        assert resp.status_code == 200
        assert user.memory_enabled is False
