from unittest.mock import AsyncMock, MagicMock

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


def test_health_check_healthy():
    mock_db = _make_mock_db()
    mock_redis = _make_mock_redis()

    async def override_db():
        yield mock_db

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_redis] = override_redis

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["postgres"] == "ok"
    assert data["redis"] == "ok"

    app.dependency_overrides.clear()


def test_health_check_postgres_down():
    mock_db = _make_mock_db()
    mock_db.execute = AsyncMock(side_effect=ConnectionError("DB down"))
    mock_redis = _make_mock_redis()

    async def override_db():
        yield mock_db

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_redis] = override_redis

    client = TestClient(app)
    response = client.get("/health")

    data = response.json()
    assert data["status"] == "degraded"
    assert data["postgres"] == "error"
    assert data["redis"] == "ok"

    app.dependency_overrides.clear()


def test_health_check_redis_down():
    mock_db = _make_mock_db()
    mock_redis = _make_mock_redis()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("Redis down"))

    async def override_db():
        yield mock_db

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_redis] = override_redis

    client = TestClient(app)
    response = client.get("/health")

    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "error"

    app.dependency_overrides.clear()
