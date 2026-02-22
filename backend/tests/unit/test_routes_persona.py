"""Smoke tests for the persona API routes.

Tests get scores, history, and alerts endpoints with mocked Redis.
"""

import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_redis
from app.main import app
from app.persona.monitor import PersonaMonitor


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.lrange = AsyncMock(return_value=[])
    return redis


@pytest.fixture
def client(mock_redis):
    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_redis] = override_redis
    # Set up shared PersonaMonitor on app state so routes can access it
    app.state.persona_monitor = PersonaMonitor(redis_client=mock_redis)
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()
    app.state.persona_monitor = None


class TestGetScores:
    def test_get_scores_found(self, client, mock_redis):
        """GET /api/v1/persona/scores should return score data."""
        score_data = {
            "scores": {
                "sycophancy": 0.1,
                "hallucination": 0.05,
                "over_confidence": 0.08,
                "safety_bypass": 0.02,
                "sales_pressure": 0.03,
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(score_data))

        resp = client.get("/api/v1/persona/scores?conversation_id=conv-1&message_id=msg-1")
        assert resp.status_code == 200
        data = resp.json()
        assert "scores" in data
        assert data["scores"]["sycophancy"] == 0.1

    def test_get_scores_not_found(self, client, mock_redis):
        """Should return null when no scores exist."""
        mock_redis.get = AsyncMock(return_value=None)

        resp = client.get("/api/v1/persona/scores?conversation_id=conv-1&message_id=msg-1")
        assert resp.status_code == 200

    def test_get_scores_requires_params(self, client):
        """Missing required params should return 422."""
        resp = client.get("/api/v1/persona/scores")
        assert resp.status_code == 422

        resp = client.get("/api/v1/persona/scores?conversation_id=conv-1")
        assert resp.status_code == 422


class TestGetHistory:
    def test_get_history_returns_list(self, client, mock_redis):
        """GET /api/v1/persona/history should return score history."""
        entries = [
            json.dumps(
                {
                    "scores": {"sycophancy": 0.1, "hallucination": 0.05},
                    "message_id": "m1",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            ),
            json.dumps(
                {
                    "scores": {"sycophancy": 0.2, "hallucination": 0.08},
                    "message_id": "m2",
                    "timestamp": "2024-01-01T00:01:00Z",
                }
            ),
        ]
        mock_redis.lrange = AsyncMock(return_value=entries)

        resp = client.get("/api/v1/persona/history?conversation_id=conv-1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["message_id"] == "m1"
        assert data[1]["message_id"] == "m2"

    def test_get_history_empty(self, client, mock_redis):
        """Should return empty list when no history exists."""
        mock_redis.lrange = AsyncMock(return_value=[])

        resp = client.get("/api/v1/persona/history?conversation_id=conv-1")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_history_requires_conversation_id(self, client):
        """Missing conversation_id should return 422."""
        resp = client.get("/api/v1/persona/history")
        assert resp.status_code == 422


class TestGetAlerts:
    def test_get_alerts_returns_high_scores(self, client, mock_redis):
        """GET /api/v1/persona/alerts should return traits above threshold."""
        entries = [
            json.dumps(
                {
                    "scores": {
                        "sycophancy": 0.8,
                        "hallucination": 0.1,
                        "over_confidence": 0.1,
                        "safety_bypass": 0.1,
                        "sales_pressure": 0.1,
                    },
                    "message_id": "m1",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            ),
        ]
        mock_redis.lrange = AsyncMock(return_value=entries)

        resp = client.get("/api/v1/persona/alerts?conversation_id=conv-1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["trait"] == "sycophancy"
        assert data[0]["score"] == 0.8

    def test_get_alerts_no_alerts(self, client, mock_redis):
        """Should return empty list when all scores are below threshold."""
        entries = [
            json.dumps(
                {
                    "scores": {
                        "sycophancy": 0.1,
                        "hallucination": 0.1,
                        "over_confidence": 0.1,
                        "safety_bypass": 0.1,
                        "sales_pressure": 0.1,
                    },
                    "message_id": "m1",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            ),
        ]
        mock_redis.lrange = AsyncMock(return_value=entries)

        resp = client.get("/api/v1/persona/alerts?conversation_id=conv-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    def test_get_alerts_requires_conversation_id(self, client):
        """Missing conversation_id should return 422."""
        resp = client.get("/api/v1/persona/alerts")
        assert resp.status_code == 422
