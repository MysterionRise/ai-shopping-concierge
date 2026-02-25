"""Tests for auto_seed.py — product catalog seeding from fixture."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.catalog.auto_seed import _compute_data_completeness, auto_seed_catalog


class TestComputeDataCompleteness:
    def test_full_data_returns_1(self):
        score = _compute_data_completeness("Moisturizer", "CeraVe", "water, glycerin", ["skincare"])
        assert score == 1.0

    def test_name_brand_ingredients_returns_05(self):
        score = _compute_data_completeness("Moisturizer", "CeraVe", "water, glycerin", [])
        assert score == 0.5

    def test_name_brand_categories_returns_05(self):
        score = _compute_data_completeness("Moisturizer", "CeraVe", "", ["skincare"])
        assert score == 0.5

    def test_minimal_data_returns_02(self):
        score = _compute_data_completeness("Moisturizer", "", "", [])
        assert score == 0.2

    def test_empty_data_returns_02(self):
        score = _compute_data_completeness("", "", "", [])
        assert score == 0.2

    def test_short_ingredients_not_counted(self):
        """Ingredients text shorter than 5 chars should not count."""
        score = _compute_data_completeness("Moisturizer", "CeraVe", "abc", [])
        assert score == 0.2

    def test_whitespace_name_not_counted(self):
        score = _compute_data_completeness("  ", "CeraVe", "water, glycerin", ["skincare"])
        assert score == 0.2


class TestAutoSeedCatalog:
    @pytest.mark.asyncio
    async def test_skips_when_products_exist(self):
        """Should return 0 if products table already has data."""
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one.return_value = 10
        session.execute = AsyncMock(return_value=result)

        inserted = await auto_seed_catalog(session)
        assert inserted == 0

    @pytest.mark.asyncio
    async def test_skips_when_fixture_missing(self):
        """Should return 0 if seed fixture file doesn't exist."""
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one.return_value = 0
        session.execute = AsyncMock(return_value=result)

        with patch("app.catalog.auto_seed.FIXTURE_PATH", Path("/nonexistent/fixture.json")):
            inserted = await auto_seed_catalog(session)
            assert inserted == 0

    @pytest.mark.asyncio
    async def test_seeds_from_fixture(self, tmp_path):
        """Should insert products from fixture when table is empty."""
        fixture = [
            {
                "openbf_code": "P001",
                "name": "Test Moisturizer",
                "brand": "TestBrand",
                "categories": ["skincare"],
                "ingredients_text": "water, glycerin, niacinamide",
                "image_url": "https://example.com/img.jpg",
            },
            {
                "openbf_code": "P002",
                "name": "Test Serum",
                "brand": "TestBrand",
                "categories": ["skincare", "serum"],
                "ingredients_text": "water, hyaluronic acid",
                "image_url": None,
            },
        ]
        fixture_path = tmp_path / "seed_fixture.json"
        fixture_path.write_text(json.dumps(fixture))

        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        session.execute = AsyncMock(return_value=count_result)
        session.add = MagicMock()

        with patch("app.catalog.auto_seed.FIXTURE_PATH", fixture_path):
            inserted = await auto_seed_catalog(session)

        assert inserted == 2
        assert session.add.call_count == 2
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_seeds_handles_missing_fields(self, tmp_path):
        """Should handle products with minimal fields."""
        fixture = [
            {
                "openbf_code": "P003",
            },
        ]
        fixture_path = tmp_path / "seed_fixture.json"
        fixture_path.write_text(json.dumps(fixture))

        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        session.execute = AsyncMock(return_value=count_result)
        session.add = MagicMock()

        with patch("app.catalog.auto_seed.FIXTURE_PATH", fixture_path):
            inserted = await auto_seed_catalog(session)

        assert inserted == 1

    @pytest.mark.asyncio
    async def test_chromadb_failure_non_fatal(self, tmp_path):
        """ChromaDB indexing failure should not prevent seeding."""
        fixture = [
            {
                "openbf_code": "P004",
                "name": "Test",
                "brand": "Test",
                "categories": [],
                "ingredients_text": "water",
            },
        ]
        fixture_path = tmp_path / "seed_fixture.json"
        fixture_path.write_text(json.dumps(fixture))

        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        session.execute = AsyncMock(return_value=count_result)
        session.add = MagicMock()

        with patch("app.catalog.auto_seed.FIXTURE_PATH", fixture_path):
            inserted = await auto_seed_catalog(session)

        # Should still return 1 even though ChromaDB import will fail
        assert inserted == 1
