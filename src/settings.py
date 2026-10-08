"""Runtime configuration loaded exclusively from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(value: str) -> list[str]:
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    model_dir: str
    cors_origins: list[str]
    api_key: str | None

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def load_settings() -> Settings:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    environment = os.getenv("ENVIRONMENT", "development").lower()
    api_key = os.getenv("API_KEY") or None
    if environment == "production" and not api_key:
        raise RuntimeError("API_KEY must be configured when ENVIRONMENT=production")

    return Settings(
        environment=environment,
        database_url=os.getenv("DATABASE_URL", os.getenv("DB_URL", "sqlite:///./data/audit_log.db")),
        model_dir=os.getenv("MODEL_DIR", os.path.join(root, "models", "pre_authorization")),
        cors_origins=_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")),
        api_key=api_key,
    )


settings = load_settings()
