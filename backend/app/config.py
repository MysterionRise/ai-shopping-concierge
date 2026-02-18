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

    # ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000

    # App
    app_host: str = "0.0.0.0"  # nosec B104
    app_port: int = 8080
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]
    llm_timeout_seconds: int = 60

    # Embeddings (optional — enables vector search in LangMem store)
    openai_api_key: str = ""

    # LangSmith (optional)
    langsmith_api_key: str = ""
    langsmith_project: str = "beauty-concierge"

    # Persona monitoring
    persona_enabled: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
