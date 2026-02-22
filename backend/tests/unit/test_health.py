from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db_session, get_redis
from app.main import app


def _make_mock_db():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    return session


def _make_mock_redis():
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()
    return redis


@pytest.fixture
def health_client():
    """TestClient with dependency overrides, cleaned up via yield."""
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_health_check_healthy(health_client):
    mock_db = _make_mock_db()
    mock_redis = _make_mock_redis()

    async def override_db():
        yield mock_db

    def override_redis():
        return mock_redis

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_redis] = override_redis

    response = health_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["postgres"] == "ok"
    assert data["redis"] == "ok"


def test_health_check_postgres_down(health_client):
    mock_db = _make_mock_db()
    mock_db.execute = AsyncMock(side_effect=ConnectionError("DB down"))
    mock_redis = _make_mock_redis()

    async def override_db():
        yield mock_db

    def override_redis():
        return mock_redis

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_redis] = override_redis

    response = health_client.get("/health")

    data = response.json()
    assert data["status"] == "degraded"
    assert data["postgres"] == "error"
    assert data["redis"] == "ok"


def test_health_check_redis_down(health_client):
    mock_db = _make_mock_db()
    mock_redis = _make_mock_redis()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("Redis down"))

    async def override_db():
        yield mock_db

    def override_redis():
        return mock_redis

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_redis] = override_redis

    response = health_client.get("/health")

    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "error"
