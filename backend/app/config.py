"""Configuration settings for Batchwise backend service."""

import os
from typing import List


class Settings:
    PROJECT_NAME: str = "Batchwise"
    TAGLINE: str = "Every batch. Every cost. Every rupee."
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # SQLite Database Configuration
    DATABASE_URL: str = os.getenv("BATCHWISE_DATABASE_URL", "sqlite:///./batchwise.db")

    # Local Ollama AI Configuration
    OLLAMA_BASE_URL: str = os.getenv("BATCHWISE_OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("BATCHWISE_OLLAMA_MODEL", "gemma3:1b")
    OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("BATCHWISE_OLLAMA_TIMEOUT", "30.0"))

    # CORS allowed origins (supports comma-separated env var for deployment)
    CORS_ORIGINS: List[str] = (
        [o.strip() for o in os.getenv("BATCHWISE_CORS_ORIGINS").split(",") if o.strip()]
        if os.getenv("BATCHWISE_CORS_ORIGINS")
        else [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )


settings = Settings()

