from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"

    PRIMARY_MODEL: str = "gpt-4o-mini"
    FALLBACK_MODEL: str = "claude-haiku-4-5-20251001"
    LLM_TIMEOUT: int = 30
    LLM_RETRIES: int = 2
    ESTIMATION_VALIDATION_RETRIES: int = 2

    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 86400
    SEMANTIC_CACHE_ENABLED: bool = True
    SEMANTIC_CACHE_LOG_ONLY: bool = False
    SEMANTIC_CACHE_THRESHOLD: float = 0.87
    SEMANTIC_CACHE_TTL: int = 86400
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    GUARDRAILS_ENABLED: bool = True

    #: Jinja prompt pack for synchronous ``POST /api/v1/estimate`` (subfolder ``estimation/<version>/``).
    ESTIMATION_PROMPT_VERSION: str = "v1"
    ESTIMATION_PROMPT_VERSIONS: str = "v1,v2"

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """LiteLLM may try either provider via fallback, so we require at least one key."""
        if self.APP_ENV != "test" and not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "At least one of OPENAI_API_KEY or ANTHROPIC_API_KEY must be set",
            )
        if not 0.85 <= self.SEMANTIC_CACHE_THRESHOLD <= 0.90:
            raise ValueError("SEMANTIC_CACHE_THRESHOLD must be between 0.85 and 0.90")
        if self.ESTIMATION_VALIDATION_RETRIES != 2:
            raise ValueError("ESTIMATION_VALIDATION_RETRIES must be exactly 2")
        return self

    @property
    def supported_prompt_versions(self) -> tuple[str, ...]:
        return tuple(
            version.strip()
            for version in self.ESTIMATION_PROMPT_VERSIONS.split(",")
            if version.strip()
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()
