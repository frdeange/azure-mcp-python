"""Tests for CacheService."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest

from azure_mcp.core.cache import CacheService, cache


class TestCacheService:
    """Tests for CacheService class."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test."""
        await cache.clear()
        yield
        await cache.clear()

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self):
        """Test that get returns None for missing key."""
        result = await cache.get("nonexistent-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test basic set and get operations."""
        await cache.set("test-key", "test-value")
        result = await cache.get("test-key")
        assert result == "test-value"

    @pytest.mark.asyncio
    async def test_invalidate(self):
        """Test invalidate operation."""
        await cache.set("test-key", "test-value")
        await cache.invalidate("test-key")
        assert await cache.get("test-key") is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_size(self):
        """Test size operation."""
        assert cache.size() == 0
        await cache.set("test-key", "value")
        assert cache.size() == 1

    @pytest.mark.asyncio
    async def test_get_or_set_with_miss(self):
        """Test get_or_set creates value on cache miss."""
        call_count = 0

        async def factory():
            nonlocal call_count
            call_count += 1
            return "computed-value"

        result = await cache.get_or_set("new-key", factory)
        assert result == "computed-value"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_get_or_set_with_hit(self):
        """Test get_or_set returns cached value on hit."""
        await cache.set("existing-key", "cached-value")
        call_count = 0

        async def factory():
            nonlocal call_count
            call_count += 1
            return "new-value"

        result = await cache.get_or_set("existing-key", factory)
        assert result == "cached-value"
        assert call_count == 0  # Factory should not be called


class TestCacheTTL:
    """Tests for cache TTL behavior."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test."""
        await cache.clear()
        yield
        await cache.clear()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test set with TTL creates entry."""
        await cache.set("ttl-key", "ttl-value", ttl=timedelta(hours=1))
        assert await cache.get("ttl-key") == "ttl-value"

    @pytest.mark.asyncio
    async def test_default_ttl(self):
        """Test that default TTL is applied."""
        await cache.set("default-ttl-key", "value")
        assert await cache.get("default-ttl-key") == "value"
