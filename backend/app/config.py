"""
Configuration management for the Market Intelligence Platform.
Uses pydantic-settings to load and validate environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str
    timescaledb_enabled: bool = True

    # Schwab API
    schwab_api_key: Optional[str] = None
    schwab_api_secret: Optional[str] = None
    schwab_callback_url: str = "http://localhost:8000/auth/callback"

    # Application
    backend_port: int = 8000
    frontend_port: int = 3000
    env: str = "development"
    log_level: str = "INFO"
    secret_key: str

    # Batch Jobs
    data_ingestion_schedule: str = "0 16 * * *"
    scoring_schedule: str = "0 17 * * *"

    # Feature Flags
    enable_sentiment: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
