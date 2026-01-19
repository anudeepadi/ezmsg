"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "EzMsg API"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ezmsg:ezmsg_dev@localhost:5433/ezmsg",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )

    # JWT Authentication
    jwt_secret: str = Field(
        default="dev-secret-change-in-prod-minimum-32-chars",
        description="JWT signing secret (minimum 32 characters in production)",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # Scheduler
    simulation_mode: bool = True
    poll_interval_seconds: int = 10
    batch_size: int = 100
    max_retry_attempts: int = 8

    # Firebase (FCM)
    firebase_credentials_path: str | None = None

    # Cookie settings
    cookie_secure: bool = False  # Set True in production with HTTPS
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
