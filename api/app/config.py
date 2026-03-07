"""Application configuration using Pydantic Settings."""

import secrets
import warnings
from functools import lru_cache
from typing import List

from pydantic import Field, model_validator
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
        default="",
        description="JWT signing secret (minimum 32 characters). Required in production.",
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
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None

    # Protocol API
    protocol_api_key: str = Field(
        default="",
        description="API key for protocol endpoints. Required for mobile integration.",
    )

    # Sentry
    sentry_dsn: str = ""

    # PII Encryption
    encryption_key: str = ""  # AES-256 key (base64-encoded 32 bytes)

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Admin seed credentials (override via env vars)
    admin_email: str = "admin@ezmsg.local"
    admin_password: str = ""

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        is_prod = self.environment == "production"

        # JWT secret: required in production, auto-generated in development
        if not self.jwt_secret:
            if is_prod:
                raise ValueError(
                    "JWT_SECRET is required in production. "
                    "Set a strong random string of at least 32 characters."
                )
            self.jwt_secret = secrets.token_urlsafe(48)
            warnings.warn(
                "JWT_SECRET not set — using an auto-generated ephemeral secret. "
                "Tokens will not survive restarts. Set JWT_SECRET for persistence.",
                stacklevel=2,
            )

        if is_prod and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production.")

        return self

    @property
    def cookie_secure(self) -> bool:
        """Cookies are always secure in production (requires HTTPS)."""
        return self.environment == "production"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
