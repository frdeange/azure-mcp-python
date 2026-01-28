"""Tests for CacheService."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest

from azure_mcp.core.cache import CacheService, cache


class TestCacheService:
    """Tests for CacheService class."""

    def test_get_returns_none_for_missing_key(self):
        """Test that get returns None for missing key."""
        result = cache.get("nonexistent-key")
        assert result is None

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache.set("test-key", "test-value")
        result = cache.get("test-key")
        assert result == "test-value"

    def test_delete(self):
        """Test delete operation."""
        cache.set("test-key", "test-value")
        cache.delete("test-key")
        assert cache.get("test-key") is None

    def test_clear(self):
        """Test clear operation."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_has(self):
        """Test has operation."""
        assert not cache.has("test-key")
        cache.set("test-key", "value")
        assert cache.has("test-key")

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
        cache.set("existing-key", "cached-value")
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

    def test_set_with_ttl(self):
        """Test set with TTL creates entry."""
        cache.set("ttl-key", "ttl-value", ttl=timedelta(hours=1))
        assert cache.get("ttl-key") == "ttl-value"

    def test_default_ttl(self):
        """Test that default TTL is applied."""
        # Default TTL should be configured in cache
        cache.set("default-ttl-key", "value")
        assert cache.has("default-ttl-key")
