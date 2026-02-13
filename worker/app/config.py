"""Worker configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Worker settings."""

    model_config = SettingsConfigDict(
        env_prefix="EZMSG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://ezmsg:ezmsg_dev@localhost:5432/ezmsg"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Worker
    poll_interval_seconds: int = 5
    batch_size: int = 50
    max_retries: int = 8
    initial_retry_delay_seconds: int = 60
    max_retry_delay_seconds: int = 3600

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # FCM (Firebase Cloud Messaging)
    fcm_credentials_path: str = ""
    firebase_credentials_json: str = ""  # JSON string for Cloud Run secrets

    # Sentry
    sentry_dsn: str = ""

    # Simulation mode (for development)
    simulation_mode: bool = True


settings = Settings()
