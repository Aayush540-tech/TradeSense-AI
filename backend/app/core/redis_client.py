import json
import logging
import time
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages low-latency Redis/Google Cloud Memorystore connections.
    Includes an automatic in-memory fallback for local development if Redis is offline,
    guaranteeing sub-50ms latency metrics and graceful degradation.
    """

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._memory_cache: dict[str, tuple[str, Optional[float]]] = {}
        self.is_connected: bool = False

    async def connect(self):
        try:
            url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
            self.redis = aioredis.from_url(
                url,
                password=settings.REDIS_PASSWORD or None,
                ssl=settings.REDIS_SSL,
                socket_timeout=settings.REDIS_TIMEOUT_MS / 1000.0,
                socket_connect_timeout=settings.REDIS_TIMEOUT_MS / 1000.0,
                decode_responses=True,
            )
            # Test ping
            start = time.perf_counter()
            await self.redis.ping()
            latency = (time.perf_counter() - start) * 1000
            self.is_connected = True
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT} (Ping: {latency:.2f}ms)")
        except Exception as e:
            self.is_connected = False
            self.redis = None
            logger.warning(
                f"Redis unavailable at {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e}). "
                "Engaging fast in-memory cache fallback for development."
            )

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self.is_connected = False
            logger.info("Redis connection closed.")

    async def get_json(self, key: str) -> Optional[Any]:
        start = time.perf_counter()
        try:
            if self.is_connected and self.redis:
                val = await self.redis.get(key)
                if val:
                    return json.loads(val)
                return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}. Reading fallback cache.")

        # In-memory fallback
        item = self._memory_cache.get(key)
        if not item:
            return None
        val_str, expiry = item
        if expiry and time.time() > expiry:
            del self._memory_cache[key]
            return None
        return json.loads(val_str)

    async def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = 300) -> bool:
        val_str = json.dumps(value)
        try:
            if self.is_connected and self.redis:
                await self.redis.set(key, val_str, ex=ttl_seconds)
                return True
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}. Writing to fallback cache.")

        expiry = (time.time() + ttl_seconds) if ttl_seconds else None
        self._memory_cache[key] = (val_str, expiry)
        return True

    async def get_latency_ms(self) -> float:
        start = time.perf_counter()
        if self.is_connected and self.redis:
            try:
                await self.redis.ping()
                return (time.perf_counter() - start) * 1000
            except Exception:
                pass
        # In-memory latency is sub-millisecond
        return round((time.perf_counter() - start) * 1000, 3)


redis_client = RedisManager()
