"""Worker configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker settings."""

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

    # FCM
    fcm_credentials_path: str = ""

    # Simulation mode (for development)
    simulation_mode: bool = True

    class Config:
        env_prefix = "EZMSG_"
        env_file = ".env"


settings = Settings()
