"""Tests for persona API routes when persona monitoring is disabled."""

import pytest
from fastapi.testclient import TestClient

from app.agents.graph import compile_graph
from app.main import app


@pytest.fixture
def client_no_persona():
    """TestClient with no persona_monitor on app state."""
    app.state.graph = compile_graph()
    # Ensure persona_monitor is not set (simulates persona_enabled=False)
    if hasattr(app.state, "persona_monitor"):
        delattr(app.state, "persona_monitor")
    return TestClient(app)


def test_scores_returns_503_when_disabled(client_no_persona):
    resp = client_no_persona.get(
        "/api/v1/persona/scores",
        params={"conversation_id": "conv-1", "message_id": "msg-1"},
    )
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()
    assert resp.headers.get("retry-after") == "30"


def test_history_returns_503_when_disabled(client_no_persona):
    resp = client_no_persona.get(
        "/api/v1/persona/history",
        params={"conversation_id": "conv-1"},
    )
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()


def test_alerts_returns_503_when_disabled(client_no_persona):
    resp = client_no_persona.get(
        "/api/v1/persona/alerts",
        params={"conversation_id": "conv-1"},
    )
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()
