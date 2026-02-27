from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4-20250514"

    # Database
    database_url: str = "postgresql+asyncpg://concierge:concierge@localhost:5432/concierge"
    database_url_sync: str = "postgresql://concierge:concierge@localhost:5432/concierge"

    # Checkpoint (psycopg format — used by langgraph-checkpoint-postgres)
    checkpoint_db_url: str = "postgresql://concierge:concierge@localhost:5432/concierge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # zvec (embedded vector store)
    zvec_collection_path: str = "./data/zvec_products"
    zvec_sparse_enabled: bool = True

    # Database tuning
    db_statement_timeout_ms: int = 30000

    # App
    app_host: str = "0.0.0.0"  # nosec B104
    app_port: int = 8080
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["Content-Type", "Authorization", "X-Request-ID", "X-User-ID"]
    llm_timeout_seconds: int = 60
    rate_limit_chat: str = "30/minute"

    # Embeddings (optional — enables vector search in LangMem store)
    openai_api_key: str = ""

    # LangSmith (optional)
    langsmith_api_key: str = ""
    langsmith_project: str = "beauty-concierge"

    # Persona monitoring
    persona_enabled: bool = False
    persona_scorer: str = "mock"  # "mock" (no ML deps) or "real" (requires torch)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
