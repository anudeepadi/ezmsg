"""Redis client singleton for session storage and caching."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None

SESSION_PREFIX = "ezmsg:session:"
SESSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours


async def get_redis() -> aioredis.Redis:
    """Get or create the Redis connection."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ── Session helpers ──────────────────────────────────────────────────────────


async def save_session(session_id: str, data: dict[str, Any]) -> None:
    """Store a protocol session in Redis with TTL."""
    try:
        r = await get_redis()
        key = f"{SESSION_PREFIX}{session_id}"
        await r.set(key, json.dumps(data), ex=SESSION_TTL_SECONDS)
    except aioredis.ConnectionError:
        logger.error("Redis connection failed while saving session %s", session_id)
        raise
    except aioredis.RedisError as e:
        logger.error("Redis error saving session %s: %s", session_id, e)
        raise


async def get_session(session_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a protocol session from Redis."""
    try:
        r = await get_redis()
        key = f"{SESSION_PREFIX}{session_id}"
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except aioredis.ConnectionError:
        logger.error("Redis connection failed while reading session %s", session_id)
        raise
    except aioredis.RedisError as e:
        logger.error("Redis error reading session %s: %s", session_id, e)
        raise


async def delete_session(session_id: str) -> bool:
    """Delete a protocol session. Returns True if it existed."""
    try:
        r = await get_redis()
        key = f"{SESSION_PREFIX}{session_id}"
        return bool(await r.delete(key))
    except aioredis.ConnectionError:
        logger.error("Redis connection failed while deleting session %s", session_id)
        raise
    except aioredis.RedisError as e:
        logger.error("Redis error deleting session %s: %s", session_id, e)
        raise
