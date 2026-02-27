"""Smoke tests for the memory API routes.

Tests get memories, delete memory, get constraints, and add constraints
endpoints with mocked LangMem store and database.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from langgraph.store.memory import InMemoryStore

from app.dependencies import get_db_session
from app.main import app
from app.memory.langmem_config import constraints_ns, user_facts_ns


@pytest.fixture
def store():
    """InMemoryStore for testing memory routes."""
    return InMemoryStore()


@pytest.fixture
def mock_db():
    session = AsyncMock()
    return session


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


@pytest.fixture
def client_no_store(mock_db):
    """Client with no store configured (store=None)."""

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db_session] = override_db
    app.state.store = None
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


class TestGetMemories:
    def test_get_memories_returns_facts_and_constraints(self, client, store):
        """GET /api/v1/users/{id}/memory should return both facts and constraints."""
        user_id = str(uuid.uuid4())

        store.put(
            user_facts_ns(user_id),
            "fact_1",
            {"content": "Has dry skin", "category": "skin_type", "created_at": "2024-01-01"},
        )
        store.put(
            constraints_ns(user_id),
            "allergy_1",
            {
                "content": "Allergic to parabens",
                "ingredient": "parabens",
                "severity": "absolute",
                "created_at": "2024-01-01",
            },
        )

        resp = client.get(
            f"/api/v1/users/{user_id}/memory",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        contents = {item["content"] for item in data}
        assert "Has dry skin" in contents
        assert "Allergic to parabens" in contents

    def test_get_memories_empty(self, client):
        """Should return empty list when user has no memories."""
        user_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/users/{user_id}/memory",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_memories_no_store(self, client_no_store):
        """Should return empty list when store is not configured."""
        user_id = str(uuid.uuid4())
        resp = client_no_store.get(
            f"/api/v1/users/{user_id}/memory",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_memories_response_shape(self, client, store):
        """Each memory should have required fields."""
        user_id = str(uuid.uuid4())
        store.put(
            user_facts_ns(user_id),
            "fact_1",
            {"content": "Test fact", "category": "preference", "created_at": "2024-01-01"},
        )

        resp = client.get(
            f"/api/v1/users/{user_id}/memory",
            headers={"X-User-ID": user_id},
        )
        data = resp.json()
        item = data[0]
        assert "id" in item
        assert "content" in item
        assert "category" in item
        assert "metadata" in item
        assert "created_at" in item


class TestDeleteMemory:
    def test_delete_memory_found(self, client, store):
        """DELETE should return deleted status when memory exists."""
        user_id = str(uuid.uuid4())
        store.put(
            user_facts_ns(user_id),
            "fact_to_delete",
            {"content": "Delete me", "category": "preference", "created_at": "2024-01-01"},
        )

        resp = client.delete(
            f"/api/v1/users/{user_id}/memory/fact_to_delete",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_memory_not_found(self, client):
        """DELETE should return not_found when memory doesn't exist."""
        user_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/users/{user_id}/memory/nonexistent",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_found"

    def test_delete_memory_no_store(self, client_no_store):
        """DELETE should return not_found when store is not configured."""
        user_id = str(uuid.uuid4())
        resp = client_no_store.delete(
            f"/api/v1/users/{user_id}/memory/any-id",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_found"


class TestGetConstraints:
    def test_get_constraints_returns_list(self, client, store):
        """GET /api/v1/users/{id}/memory/constraints should return constraints."""
        user_id = str(uuid.uuid4())
        store.put(
            constraints_ns(user_id),
            "allergy_fragrance",
            {
                "content": "fragrance",
                "ingredient": "fragrance",
                "severity": "absolute",
                "created_at": "2024-01-01",
            },
        )

        resp = client.get(
            f"/api/v1/users/{user_id}/memory/constraints",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["category"] == "constraints"

    def test_get_constraints_empty(self, client):
        """Should return empty list when user has no constraints."""
        user_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/users/{user_id}/memory/constraints",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_constraints_no_store(self, client_no_store):
        """Should return empty list when store is not configured."""
        user_id = str(uuid.uuid4())
        resp = client_no_store.get(
            f"/api/v1/users/{user_id}/memory/constraints",
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestAddConstraint:
    @patch("app.api.routes.memory.add_constraint")
    def test_add_hard_constraint(self, mock_add_constraint, client, store):
        """POST /api/v1/users/{id}/memory/constraints should add a hard constraint."""
        mock_add_constraint.return_value = None
        user_id = str(uuid.uuid4())

        resp = client.post(
            f"/api/v1/users/{user_id}/memory/constraints",
            json={"constraint": "paraben", "is_hard": True},
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "created"
        assert "id" in data

        # Verify constraint was stored in the LangMem store
        items = store.search(constraints_ns(user_id))
        assert len(items) == 1
        assert items[0].value["ingredient"] == "paraben"
        assert items[0].value["severity"] == "absolute"

    @patch("app.api.routes.memory.add_constraint")
    def test_add_soft_constraint(self, mock_add_constraint, client, store):
        """Soft constraint should go to user_facts namespace."""
        mock_add_constraint.return_value = None
        user_id = str(uuid.uuid4())

        resp = client.post(
            f"/api/v1/users/{user_id}/memory/constraints",
            json={"constraint": "vegan", "is_hard": False},
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200

        items = store.search(user_facts_ns(user_id))
        assert len(items) == 1
        assert items[0].value["severity"] == "preference"

    @patch("app.api.routes.memory.add_constraint")
    def test_add_constraint_calls_db_persist(self, mock_add_constraint, client, mock_db):
        """add_constraint should be called to persist to Postgres."""
        mock_add_constraint.return_value = None
        user_id = str(uuid.uuid4())

        resp = client.post(
            f"/api/v1/users/{user_id}/memory/constraints",
            json={"constraint": "sulfate", "is_hard": True},
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 200
        mock_add_constraint.assert_called_once()
        call_args = mock_add_constraint.call_args
        assert call_args[0][1] == user_id
        assert call_args[0][2] == "sulfate"

    def test_add_constraint_missing_fields(self, client):
        """Missing constraint field should return 422."""
        user_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/users/{user_id}/memory/constraints",
            json={"is_hard": True},
            headers={"X-User-ID": user_id},
        )
        assert resp.status_code == 422
