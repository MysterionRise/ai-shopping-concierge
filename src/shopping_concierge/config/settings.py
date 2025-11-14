"""Configuration settings for the Shopping Concierge application."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic API Configuration
    anthropic_api_key: str
    claude_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Application Configuration
    log_level: str = "INFO"
    environment: str = "development"

    # Agent Configuration
    max_iterations: int = 5
    timeout_seconds: int = 30

    # Mock Data Configuration
    use_mock_data: bool = True
    mock_delay_seconds: float = 0.5


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
