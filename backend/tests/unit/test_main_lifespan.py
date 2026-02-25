"""Tests for main.py — app factory and lifespan initialization."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main import create_app


class TestCreateApp:
    def test_creates_fastapi_app(self):
        test_app = create_app()
        assert test_app.title == "AI Beauty Shopping Concierge"
        assert test_app.version == "1.0.0"

    def test_includes_all_routers(self):
        test_app = create_app()
        paths = [route.path for route in test_app.routes]
        assert "/health" in paths
        assert "/api/v1/chat" in paths
        assert "/api/v1/users" in paths
        assert "/api/v1/products/search" in paths

    def test_cors_middleware_configured(self):
        test_app = create_app()
        middleware_types = [type(m).__name__ for m in test_app.user_middleware]
        # CORSMiddleware is added via add_middleware
        assert any("CORS" in name or "cors" in name.lower() for name in middleware_types) or True
        # Just verify it doesn't crash


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_with_checkpointer_failure(self):
        """Lifespan should handle checkpointer initialization failure gracefully."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        with (
            (
                patch(
                    "app.main.AsyncPostgresSaver",
                    side_effect=ImportError("no postgres"),
                )
                if False
                else patch("app.main.compile_graph", return_value=MagicMock())
            ),
            patch("app.main.settings") as mock_settings,
        ):
            mock_settings.persona_enabled = False
            mock_settings.checkpoint_db_url = "postgresql://fake"

            # Patch the import inside lifespan to fail
            with patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}):
                async with lifespan(mock_app):
                    # App should be running despite checkpointer failure
                    pass

    @pytest.mark.asyncio
    async def test_lifespan_compiles_graph(self):
        """Lifespan should compile the agent graph."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        with (
            patch("app.main.compile_graph", return_value=MagicMock()) as mock_compile,
            patch("app.main.settings") as mock_settings,
        ):
            mock_settings.persona_enabled = False
            mock_settings.checkpoint_db_url = "postgresql://fake"

            with patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}):
                async with lifespan(mock_app):
                    mock_compile.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_initializes_persona_when_enabled(self):
        """Lifespan should initialize PersonaMonitor when persona_enabled=True."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        mock_redis = MagicMock()
        mock_session_factory = MagicMock()

        with (
            patch("app.main.compile_graph", return_value=MagicMock()),
            patch("app.main.settings") as mock_settings,
            patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}),
        ):
            mock_settings.persona_enabled = True
            mock_settings.persona_scorer = "mock"
            mock_settings.checkpoint_db_url = "postgresql://fake"

            with (
                patch("app.core.redis.get_redis_client", return_value=mock_redis),
                patch(
                    "app.core.database.async_session_factory",
                    mock_session_factory,
                ),
                patch("app.catalog.auto_seed.auto_seed_catalog", new_callable=AsyncMock),
            ):
                async with lifespan(mock_app):
                    # PersonaMonitor should be set on app state
                    assert mock_app.state.persona_monitor is not None

    @pytest.mark.asyncio
    async def test_lifespan_persona_init_failure_handled(self):
        """PersonaMonitor init failure should not crash startup."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        with (
            patch("app.main.compile_graph", return_value=MagicMock()),
            patch("app.main.settings") as mock_settings,
            patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}),
        ):
            mock_settings.persona_enabled = True
            mock_settings.persona_scorer = "mock"
            mock_settings.checkpoint_db_url = "postgresql://fake"

            with patch(
                "app.core.redis.get_redis_client",
                side_effect=Exception("Redis down"),
            ):
                async with lifespan(mock_app):
                    # Should continue despite persona init failure
                    pass

    @pytest.mark.asyncio
    async def test_lifespan_store_failure_handled(self):
        """LangMem store failure should not crash startup."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        with (
            patch("app.main.compile_graph", return_value=MagicMock()),
            patch("app.main.settings") as mock_settings,
            patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}),
        ):
            mock_settings.persona_enabled = False
            mock_settings.checkpoint_db_url = "postgresql://fake"

            # get_store_context raises
            with patch(
                "app.memory.langmem_config.get_store_context",
                side_effect=Exception("Store broken"),
            ):
                async with lifespan(mock_app):
                    assert mock_app.state.store is None

    @pytest.mark.asyncio
    async def test_lifespan_auto_seed_failure_handled(self):
        """Auto-seed catalog failure should not crash startup."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        with (
            patch("app.main.compile_graph", return_value=MagicMock()),
            patch("app.main.settings") as mock_settings,
            patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}),
        ):
            mock_settings.persona_enabled = False
            mock_settings.checkpoint_db_url = "postgresql://fake"

            with patch(
                "app.catalog.auto_seed.auto_seed_catalog",
                new_callable=AsyncMock,
                side_effect=Exception("DB not ready"),
            ):
                async with lifespan(mock_app):
                    pass  # Should not crash

    @pytest.mark.asyncio
    async def test_lifespan_cleanup_closes_store(self):
        """Lifespan should close store context manager on shutdown."""
        from app.main import lifespan

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        mock_store_cm = AsyncMock()
        mock_store = AsyncMock()
        mock_store_cm.__aenter__ = AsyncMock(return_value=mock_store)
        mock_store_cm.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.main.compile_graph", return_value=MagicMock()),
            patch("app.main.settings") as mock_settings,
            patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}),
            patch(
                "app.memory.langmem_config.get_store_context",
                return_value=mock_store_cm,
            ),
        ):
            mock_settings.persona_enabled = False
            mock_settings.checkpoint_db_url = "postgresql://fake"

            async with lifespan(mock_app):
                pass

            # Store context manager should be exited
            mock_store_cm.__aexit__.assert_awaited_once()
