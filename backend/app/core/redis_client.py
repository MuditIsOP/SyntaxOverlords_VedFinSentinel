"""
Redis Client — Graceful degradation when Redis is unavailable.

Provides async get/set with automatic fallback to no-op when Redis is down.
"""
import json
import structlog
from typing import Optional
from app.core.config import settings

logger = structlog.get_logger()

_redis_client = None
_redis_available = False


async def get_redis():
    """Get or create the Redis connection."""
    global _redis_client, _redis_available
    
    if _redis_client is not None:
        return _redis_client if _redis_available else None
    
    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2
        )
        # Test connectivity
        await _redis_client.ping()
        _redis_available = True
        logger.info("redis_connected", url=settings.REDIS_URL)
        return _redis_client
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e), fallback="no_cache")
        _redis_available = False
        return None


async def cache_get(key: str) -> Optional[str]:
    """Get a value from Redis cache. Returns None if Redis is unavailable."""
    r = await get_redis()
    if r is None:
        return None
    try:
        return await r.get(key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl_seconds: int = 3600) -> bool:
    """Set a value in Redis cache. Returns False if Redis is unavailable."""
    r = await get_redis()
    if r is None:
        return False
    try:
        await r.setex(key, ttl_seconds, value)
        return True
    except Exception:
        return False


async def cache_get_json(key: str) -> Optional[dict]:
    """Get and parse a JSON value from Redis."""
    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


async def cache_set_json(key: str, data: dict, ttl_seconds: int = 3600) -> bool:
    """Serialize and set a JSON value in Redis."""
    return await cache_set(key, json.dumps(data), ttl_seconds)
