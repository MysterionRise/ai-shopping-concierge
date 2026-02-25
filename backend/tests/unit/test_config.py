from app.config import Settings


def test_default_settings():
    s = Settings(
        openrouter_api_key="test",
        database_url="postgresql+asyncpg://test:test@localhost/test",
        database_url_sync="postgresql://test:test@localhost/test",
    )
    assert s.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert s.app_port == 8080
    assert s.persona_enabled is False
    assert s.persona_scorer == "mock"
    assert "http://localhost:3000" in s.cors_origins
    assert s.db_statement_timeout_ms == 30000


def test_settings_log_level():
    s = Settings(
        openrouter_api_key="test",
        log_level="DEBUG",
        database_url="postgresql+asyncpg://test:test@localhost/test",
        database_url_sync="postgresql://test:test@localhost/test",
    )
    assert s.log_level == "DEBUG"
