"""
Configuration utilities for Streamlit frontend.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


def get_api_url() -> str:
    """Get the backend API URL from environment or default."""
    backend_port = os.getenv("BACKEND_PORT", "8000")
    return f"http://localhost:{backend_port}"


def get_frontend_port() -> int:
    """Get the frontend port from environment or default."""
    return int(os.getenv("FRONTEND_PORT", "8501"))
