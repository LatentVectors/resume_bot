"""Configuration management for the resume bot."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unexpected env vars rather than erroring
    )

    # Database
    database_url: str = Field(default="sqlite:///data/resume_bot.db")

    # LangChain / LLM providers
    openai_api_key: str | None = Field(default=None)
    langchain_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)

    # LangSmith / tracing
    langsmith_tracing: bool = Field(default=False)
    langsmith_endpoint: str | None = Field(default=None)
    langsmith_api_key: str | None = Field(default=None)
    langsmith_project: str | None = Field(default=None)

    # App
    app_name: str = Field(default="Resume Bot")
    debug: bool = Field(default=False)
    app_base_url: str = Field(default="http://localhost:8501")

    # Paths
    data_dir: Path = Field(default=Path("data"))


def load_settings() -> Settings:
    """Load settings from environment variables."""
    # Load from .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    settings = Settings()

    # Ensure data directory exists
    settings.data_dir.mkdir(exist_ok=True)

    return settings


# Global settings instance
settings = load_settings()
