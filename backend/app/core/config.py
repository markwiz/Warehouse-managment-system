"""Application settings loaded from environment variables / .env."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Works whether the app is started from the repo root or from backend/.
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Warehouse Management System"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Database
    database_url: str = "postgresql+psycopg://wms:wms@localhost:5432/wms"
    # Used only by the test suite; defaults to "<database>_test" on the same server.
    test_database_url: str | None = None

    # LLM (LangChain / LangGraph)
    anthropic_api_key: str | None = None
    llm_model: str = "claude-opus-5-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
