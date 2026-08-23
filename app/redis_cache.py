from __future__ import annotations

import json
import logging

from app.models import SamplesResponse

logger = logging.getLogger(__name__)

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None  # type: ignore[assignment,misc]


class RedisCache:
    """Async Redis wrapper for SamplesResponse caching."""

    def __init__(self, url: str, ttl: int = 60 * 60 * 24) -> None:
        if not Redis:
            raise RuntimeError("redis package not installed")
        self._redis: Redis = Redis.from_url(url, decode_responses=True)
        self._ttl = ttl

    async def get(self, key: str) -> SamplesResponse | None:
        try:
            raw = await self._redis.get(f"sample:{key}")
        except Exception:
            logger.warning("Redis GET failed for %s", key, exc_info=True)
            return None
        if raw is None:
            return None
        try:
            return SamplesResponse.model_validate_json(raw)
        except Exception:
            return None

    async def set(self, key: str, response: SamplesResponse) -> None:
        try:
            await self._redis.set(
                f"sample:{key}",
                response.model_dump_json(),
                ex=self._ttl,
            )
        except Exception:
            logger.warning("Redis SET failed for %s", key, exc_info=True)

    async def close(self) -> None:
        await self._redis.aclose()


class NullCache:
    """No-op fallback when Redis is not configured."""

    async def get(self, key: str) -> SamplesResponse | None:
        return None

    async def set(self, key: str, response: SamplesResponse) -> None:
        pass

    async def close(self) -> None:
        pass


def build_cache(url: str, ttl: int = 60 * 60 * 24) -> RedisCache | NullCache:
    if not url:
        logger.info("No REDIS_URL — using in-process NullCache")
        return NullCache()
    return RedisCache(url, ttl)
