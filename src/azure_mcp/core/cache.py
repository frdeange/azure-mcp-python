"""In-memory caching utilities.

Provides TTL-based caching for Azure resource resolution.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cached value with expiration time."""

    value: Any
    expires_at: datetime


class CacheService:
    """
    Simple in-memory cache with TTL support.

    Thread-safe for async operations.
    """

    def __init__(self) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        ttl: timedelta = timedelta(hours=1),
    ) -> T:
        """
        Get from cache or compute and cache the value.

        Args:
            key: Cache key.
            factory: Async function to compute value if not cached.
            ttl: Time-to-live for the cached value.

        Returns:
            The cached or newly computed value.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry and entry.expires_at > datetime.utcnow():
                return entry.value

            value = await factory()
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=datetime.utcnow() + ttl,
            )
            return value

    async def get(self, key: str) -> Any | None:
        """Get a value from cache if it exists and is not expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry and entry.expires_at > datetime.utcnow():
                return entry.value
            return None

    async def set(
        self,
        key: str,
        value: T,
        ttl: timedelta = timedelta(hours=1),
    ) -> None:
        """Set a value in cache with TTL."""
        async with self._lock:
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=datetime.utcnow() + ttl,
            )

    async def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cached entries."""
        async with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get the number of entries in cache."""
        return len(self._cache)


# Global cache instance
cache = CacheService()
