"""
Redis Cache Layer for User Baselines and Performance Optimization.
Provides sub-millisecond access to frequently-used user baselines.
"""
import json
import pickle
from typing import Optional, Dict, Any
from datetime import timedelta

import redis.asyncio as redis
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Cache TTL settings
BASELINE_TTL_SECONDS = 300  # 5 minutes for baselines
METRICS_TTL_SECONDS = 60    # 1 minute for metrics
TRANSACTION_TTL_SECONDS = 600  # 10 minutes for transaction lookups


class RedisCache:
    """Singleton Redis cache manager."""

    _instance = None
    _redis: Optional[redis.Redis] = None
    _enabled = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
        return cls._instance

    async def connect(self):
        """Initialize Redis connection."""
        if self._redis is None and self._enabled:
            try:
                self._redis = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False  # We'll handle decoding manually for flexibility
                )
                await self._redis.ping()
                logger.info("redis_connected", url=settings.REDIS_URL)
            except Exception as e:
                logger.error("redis_connection_failed", error=str(e))
                self._enabled = False
                self._redis = None

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("redis_disconnected")

    def _get_baseline_key(self, user_id: str) -> str:
        return f"baseline:{user_id}"

    def _get_metrics_key(self, window: str) -> str:
        return f"metrics:{window}"

    def _get_txn_key(self, txn_id: str) -> str:
        return f"txn:{txn_id}"

    async def get_user_baseline(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user baseline from Redis."""
        if not self._enabled or not self._redis:
            return None

        try:
            key = self._get_baseline_key(user_id)
            data = await self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.warning("redis_get_baseline_failed", error=str(e), user_id=user_id)
            return None

    async def set_user_baseline(self, user_id: str, baseline: Dict[str, Any]) -> bool:
        """Cache user baseline in Redis."""
        if not self._enabled or not self._redis:
            return False

        try:
            key = self._get_baseline_key(user_id)
            serialized = pickle.dumps(baseline)
            await self._redis.setex(key, BASELINE_TTL_SECONDS, serialized)
            logger.debug("baseline_cached", user_id=user_id, ttl=BASELINE_TTL_SECONDS)
            return True
        except Exception as e:
            logger.warning("redis_set_baseline_failed", error=str(e), user_id=user_id)
            return False

    async def invalidate_baseline(self, user_id: str) -> bool:
        """Invalidate cached baseline (e.g., after update)."""
        if not self._enabled or not self._redis:
            return False

        try:
            key = self._get_baseline_key(user_id)
            await self._redis.delete(key)
            logger.debug("baseline_invalidated", user_id=user_id)
            return True
        except Exception as e:
            logger.warning("redis_invalidate_failed", error=str(e), user_id=user_id)
            return False

    async def get_metrics(self, window: str) -> Optional[Dict[str, Any]]:
        """Get cached metrics."""
        if not self._enabled or not self._redis:
            return None

        try:
            key = self._get_metrics_key(window)
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning("redis_get_metrics_failed", error=str(e))
            return None

    async def set_metrics(self, window: str, metrics: Dict[str, Any]) -> bool:
        """Cache metrics."""
        if not self._enabled or not self._redis:
            return False

        try:
            key = self._get_metrics_key(window)
            await self._redis.setex(key, METRICS_TTL_SECONDS, json.dumps(metrics))
            return True
        except Exception as e:
            logger.warning("redis_set_metrics_failed", error=str(e))
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health and return stats."""
        if not self._enabled or not self._redis:
            return {"status": "disabled", "connected": False}

        try:
            info = await self._redis.info()
            return {
                "status": "healthy",
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {"status": "error", "connected": False, "error": str(e)}


# Global instance
cache = RedisCache()
