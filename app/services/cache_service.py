"""Redis-backed caching and ephemeral key-value storage."""

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class CacheService:
    """Thin wrapper around Redis for caching and transient state."""

    def __init__(self) -> None:
        self._client = redis.from_url(str(settings.redis_url), decode_responses=True)

    async def get(self, key: str) -> Any | None:
        """Retrieve and deserialize a cached value, or None if absent."""
        value = await self._client.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Serialize and store a value, with an optional expiry."""
        await self._client.set(key, json.dumps(value), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Return True if the key is present."""
        return bool(await self._client.exists(key))

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        await self._client.close()


cache_service = CacheService()