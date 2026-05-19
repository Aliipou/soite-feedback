"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration. Never hardcode secrets — use .env or environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    environment: Literal["development", "staging", "production"] = "development"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str
    pgcrypto_key: str

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Security
    secret_key: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Admin seed
    admin_email: str = "admin@soite.fi"

    @field_validator("secret_key")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 64:
            msg = "SECRET_KEY must be at least 64 hex characters (32 bytes)"
            raise ValueError(msg)
        return v

    @field_validator("pgcrypto_key")
    @classmethod
    def pgcrypto_key_min_length(cls, v: str) -> str:
        if len(v) < 64:
            msg = "PGCRYPTO_KEY must be at least 64 hex characters (32 bytes)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def keys_must_differ(self) -> "Settings":
        if self.secret_key == self.pgcrypto_key:
            msg = "SECRET_KEY and PGCRYPTO_KEY must be different values"
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance. Import this, not Settings directly."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
