"""
Configuration management for the Market Intelligence Platform.
Uses pydantic-settings to load and validate environment variables.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv

# Get project root directory (2 levels up from this file)
# Must resolve __file__ first before getting parents
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables from .env file
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str

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

    # CORS — set CORS_ORIGINS=["https://your-app.streamlit.app"] in production
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
