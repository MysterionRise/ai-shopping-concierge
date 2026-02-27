"""Tests for zvec-based vector store."""

from unittest.mock import patch

import pytest

from app.core.vector_store import (
    initialize_zvec,
    optimize_collection,
    reset,
    search_hybrid,
    search_similar,
    upsert_product,
)


def _try_init_zvec(path: str) -> bool:
    """Try to initialize zvec; return False if native module is broken."""
    try:
        with patch("app.core.vector_store.settings") as mock_settings:
            mock_settings.zvec_collection_path = path
            mock_settings.zvec_sparse_enabled = False
            initialize_zvec(collection_path=path)
        return True
    except (ImportError, ModuleNotFoundError):
        pytest.skip("zvec native module not available")
        return False


@pytest.fixture(autouse=True)
def clean_state():
    """Reset vector store module state between tests."""
    reset()
    yield
    reset()


@pytest.fixture
def zvec_collection(tmp_path):
    """Initialize a temporary zvec collection for testing."""
    path = str(tmp_path / "test_collection")
    _try_init_zvec(path)
    return path


class TestInitialize:
    def test_initialize_creates_collection(self, tmp_path):
        path = str(tmp_path / "new_collection")
        _try_init_zvec(path)
        # Should be able to search without error
        results = search_similar("test query")
        assert isinstance(results, list)

    def test_open_existing_collection(self, tmp_path):
        """Test that an existing collection can be reopened."""
        path = str(tmp_path / "persist_collection")
        _try_init_zvec(path)
        upsert_product("p1", "Moisturizer", "CeraVe", "water, glycerin")
        optimize_collection()

        # Reset and reopen
        reset()
        _try_init_zvec(path)

        results = search_similar("moisturizer")
        assert len(results) >= 1
        assert results[0]["id"] == "p1"


class TestUpsertAndSearch:
    def test_upsert_and_search_dense(self, zvec_collection):
        upsert_product("p1", "Hydrating Moisturizer", "CeraVe", "water, glycerin, hyaluronic acid")
        results = search_similar("moisturizer for dry skin")
        assert len(results) == 1
        assert results[0]["id"] == "p1"
        assert results[0]["metadata"]["name"] == "Hydrating Moisturizer"
        assert results[0]["metadata"]["brand"] == "CeraVe"
        assert "distance" in results[0]

    def test_search_returns_ranked_results(self, zvec_collection):
        upsert_product("p1", "Hydrating Moisturizer", "CeraVe", "water, glycerin, hyaluronic acid")
        upsert_product(
            "p2", "Vitamin C Serum", "TruSkin", "ascorbic acid, vitamin e, hyaluronic acid"
        )
        upsert_product("p3", "Retinol Night Cream", "Neutrogena", "retinol, shea butter")

        results = search_similar("vitamin c brightening serum")
        assert len(results) == 3
        # p2 (vitamin C serum) should be the best match
        assert results[0]["id"] == "p2"

    def test_search_empty_collection(self, zvec_collection):
        results = search_similar("anything")
        assert results == []

    def test_search_not_initialized_returns_empty(self):
        """Search on uninitialized store should return empty list."""
        results = search_similar("test")
        assert results == []

    def test_upsert_not_initialized_is_noop(self):
        """Upsert on uninitialized store should not raise."""
        upsert_product("p1", "Test", "Brand", "water")  # Should not raise

    def test_search_n_results_limits(self, zvec_collection):
        for i in range(5):
            upsert_product(f"p{i}", f"Product {i}", "Brand", "water, glycerin")
        results = search_similar("product", n_results=3)
        assert len(results) == 3


class TestHybridSearch:
    def test_hybrid_falls_back_to_dense_when_sparse_disabled(self, zvec_collection):
        """When sparse is disabled, hybrid should still work (dense-only)."""
        upsert_product("p1", "Moisturizer", "CeraVe", "water, glycerin")
        results = search_hybrid("moisturizer")
        assert len(results) == 1
        assert results[0]["id"] == "p1"

    def test_hybrid_empty_collection_returns_empty(self, zvec_collection):
        results = search_hybrid("anything")
        assert results == []

    def test_hybrid_not_initialized_returns_empty(self):
        results = search_hybrid("test")
        assert results == []


class TestOptimize:
    def test_optimize_not_initialized_is_noop(self):
        optimize_collection()  # Should not raise

    def test_optimize_after_upserts(self, zvec_collection):
        upsert_product("p1", "Product", "Brand", "water")
        optimize_collection()  # Should not raise
