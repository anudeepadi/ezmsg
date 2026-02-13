"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Use Redis for rate limit storage in production (multi-replica safe),
# fall back to in-memory storage in development.
_storage_uri = settings.redis_url if settings.is_production else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri=_storage_uri,
)
