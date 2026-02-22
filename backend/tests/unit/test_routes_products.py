"""Smoke tests for the products API routes.

Tests search products and get product endpoints with mocked database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db_session
from app.main import app


def _make_mock_product(**overrides):
    """Create a mock Product ORM object."""
    product = MagicMock()
    product.id = overrides.get("id", uuid.uuid4())
    product.openbf_code = overrides.get("openbf_code", "OBF12345")
    product.name = overrides.get("name", "Gentle Moisturizer")
    product.brand = overrides.get("brand", "TestBrand")
    product.categories = overrides.get("categories", ["moisturizers"])
    product.ingredients = overrides.get("ingredients", ["water", "glycerin"])
    product.ingredients_text = overrides.get("ingredients_text", "Water, Glycerin")
    product.image_url = overrides.get("image_url", None)
    product.safety_score = overrides.get("safety_score", 9.0)
    product.created_at = datetime.now(timezone.utc)
    product.updated_at = datetime.now(timezone.utc)
    return product


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


class TestSearchProducts:
    def test_search_returns_list(self, client, mock_db):
        """GET /api/v1/products/search should return a list of products."""
        p1 = _make_mock_product(name="Moisturizer A")
        p2 = _make_mock_product(name="Moisturizer B", openbf_code="OBF99999")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p1, p2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get("/api/v1/products/search?q=moisturizer")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Moisturizer A"
        assert data[1]["name"] == "Moisturizer B"

    def test_search_empty_query_returns_results(self, client, mock_db):
        """Empty query should still return products (no filter)."""
        p = _make_mock_product()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p]
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get("/api/v1/products/search")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_search_no_results(self, client, mock_db):
        """Search with no matching products should return empty list."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get("/api/v1/products/search?q=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_response_shape(self, client, mock_db):
        """Each product in search results should have required fields."""
        p = _make_mock_product()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p]
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get("/api/v1/products/search?q=test")
        data = resp.json()
        product = data[0]
        assert "id" in product
        assert "openbf_code" in product
        assert "name" in product
        assert "brand" in product
        assert "categories" in product
        assert "ingredients" in product
        assert "safety_score" in product


class TestGetProduct:
    def test_get_product_found(self, client, mock_db):
        """GET /api/v1/products/{id} should return product when found."""
        product = _make_mock_product(name="Good Serum", brand="SerumCo")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = product
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/products/{product.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Good Serum"
        assert data["brand"] == "SerumCo"
        assert data["safety_score"] == 9.0

    def test_get_product_not_found(self, client, mock_db):
        """GET /api/v1/products/{id} should return 404 when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = client.get(f"/api/v1/products/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Product not found"
