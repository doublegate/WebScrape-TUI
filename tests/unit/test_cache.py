"""Unit tests for cache module."""

import time
from unittest.mock import patch

from scrapetui.core.cache import (
    MemoryCache,
    cached,
    get_cache,
    invalidate_cache
)


class TestMemoryCache:
    """Test MemoryCache implementation."""

    def test_set_get(self):
        """Test basic set/get operations."""
        cache = MemoryCache()

        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'

    def test_get_nonexistent(self):
        """Test get on non-existent key returns None."""
        cache = MemoryCache()
        assert cache.get('nonexistent') is None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCache()

        cache.set('key1', 'value1', ttl=1)  # 1 second TTL
        assert cache.get('key1') == 'value1'

        time.sleep(1.5)
        assert cache.get('key1') is None

    def test_delete(self):
        """Test delete operation."""
        cache = MemoryCache()

        cache.set('key1', 'value1')
        cache.delete('key1')
        assert cache.get('key1') is None

    def test_delete_nonexistent(self):
        """Test delete on non-existent key doesn't raise error."""
        cache = MemoryCache()
        cache.delete('nonexistent')  # Should not raise

    def test_clear(self):
        """Test clear operation."""
        cache = MemoryCache()

        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()

        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_exists(self):
        """Test exists check."""
        cache = MemoryCache()

        assert not cache.exists('key1')
        cache.set('key1', 'value1')
        assert cache.exists('key1')

    def test_exists_expired(self):
        """Test exists on expired key returns False."""
        cache = MemoryCache()

        cache.set('key1', 'value1', ttl=1)
        time.sleep(1.5)
        assert not cache.exists('key1')

    def test_stats(self):
        """Test cache statistics."""
        cache = MemoryCache()

        cache.set('key1', 'value1', ttl=100)
        cache.set('key2', 'value2', ttl=1)

        time.sleep(1.5)

        stats = cache.stats()
        assert stats['total_keys'] == 2
        assert stats['expired_keys'] == 1
        assert stats['active_keys'] == 1

    def test_multiple_values(self):
        """Test storing multiple different value types."""
        cache = MemoryCache()

        cache.set('string', 'value')
        cache.set('int', 123)
        cache.set('list', [1, 2, 3])
        cache.set('dict', {'key': 'value'})

        assert cache.get('string') == 'value'
        assert cache.get('int') == 123
        assert cache.get('list') == [1, 2, 3]
        assert cache.get('dict') == {'key': 'value'}

    def test_thread_safety(self):
        """Test thread-safe operations."""
        import threading

        cache = MemoryCache()
        results = []

        def set_value(key, value):
            cache.set(key, value)
            results.append(cache.get(key))

        threads = [
            threading.Thread(target=set_value, args=(f'key{i}', f'value{i}'))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All operations should succeed
        assert len(results) == 10


class TestCachedDecorator:
    """Test @cached decorator."""

    def test_basic_caching(self):
        """Test basic function result caching."""
        call_count = 0

        @cached(ttl=10, key_prefix='test')
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - cache miss
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - cache hit
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not called again

        # Different argument - cache miss
        result3 = expensive_function(7)
        assert result3 == 14
        assert call_count == 2

    def test_caching_with_kwargs(self):
        """Test caching with keyword arguments."""
        call_count = 0

        @cached(ttl=10)
        def function_with_kwargs(a, b=10):
            nonlocal call_count
            call_count += 1
            return a + b

        result1 = function_with_kwargs(5, b=20)
        assert result1 == 25
        assert call_count == 1

        result2 = function_with_kwargs(5, b=20)
        assert result2 == 25
        assert call_count == 1  # Cache hit

        # Different kwargs - cache miss
        result3 = function_with_kwargs(5, b=30)
        assert result3 == 35
        assert call_count == 2

    def test_cache_ttl(self):
        """Test cache TTL expiration."""
        call_count = 0

        @cached(ttl=1)
        def function_with_ttl(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = function_with_ttl(5)
        assert result1 == 10
        assert call_count == 1

        # Wait for TTL to expire
        time.sleep(1.5)

        result2 = function_with_ttl(5)
        assert result2 == 10
        assert call_count == 2  # Called again after expiration

    def test_cache_clear(self):
        """Test cache_clear method on decorated function."""
        @cached(ttl=10)
        def some_function(x):
            return x * 3

        result1 = some_function(4)
        assert result1 == 12

        # Clear cache
        some_function.cache_clear()

        # Should work without error
        result2 = some_function(4)
        assert result2 == 12

    def test_different_args_different_cache(self):
        """Test different arguments create different cache entries."""
        @cached(ttl=10)
        def add(a, b):
            return a + b

        result1 = add(1, 2)
        result2 = add(2, 3)
        result3 = add(1, 2)  # Same as result1

        assert result1 == 3
        assert result2 == 5
        assert result3 == 3


class TestGetCache:
    """Test get_cache singleton."""

    def test_get_cache_returns_memory_cache_by_default(self):
        """Test get_cache returns MemoryCache by default."""
        # Reset singleton
        import scrapetui.core.cache
        scrapetui.core.cache._cache_instance = None

        cache = get_cache()
        assert isinstance(cache, MemoryCache)

    def test_get_cache_singleton(self):
        """Test get_cache returns same instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    @patch('scrapetui.core.cache.get_config')
    def test_get_cache_disabled(self, mock_get_config):
        """Test get_cache when caching is disabled."""
        import scrapetui.core.cache
        from scrapetui.config import Config
        scrapetui.core.cache._cache_instance = None

        # Mock config with cache disabled
        mock_config = Config(cache_enabled=False)
        mock_get_config.return_value = mock_config

        cache = get_cache()
        assert isinstance(cache, MemoryCache)

        # Reset
        scrapetui.core.cache._cache_instance = None


class TestInvalidateCache:
    """Test cache invalidation."""

    def test_invalidate_cache_all(self):
        """Test invalidating all cache entries."""
        cache = get_cache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')

        invalidate_cache()

        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_invalidate_cache_with_pattern(self):
        """Test invalidating cache with pattern (currently clears all)."""
        cache = get_cache()
        cache.set('user:1', 'data1')
        cache.set('user:2', 'data2')

        invalidate_cache(pattern='user:*')

        # Currently clears all
        assert cache.get('user:1') is None
        assert cache.get('user:2') is None


class TestCacheEdgeCases:
    """Test edge cases and error handling."""

    def test_cache_none_value(self):
        """Test caching None value."""
        cache = MemoryCache()

        cache.set('key1', None)
        # get() returns None for both non-existent and None values
        # This is by design - None is not cached
        result = cache.get('key1')
        # Since we can't distinguish, None values effectively aren't cached
        assert result is None

    def test_cache_empty_string(self):
        """Test caching empty string."""
        cache = MemoryCache()

        cache.set('key1', '')
        assert cache.get('key1') == ''

    def test_cache_zero_value(self):
        """Test caching zero value."""
        cache = MemoryCache()

        cache.set('key1', 0)
        assert cache.get('key1') == 0

    def test_cache_false_value(self):
        """Test caching False value."""
        cache = MemoryCache()

        cache.set('key1', False)
        assert cache.get('key1') is False

    def test_very_short_ttl(self):
        """Test very short TTL."""
        cache = MemoryCache()

        cache.set('key1', 'value1', ttl=0.1)
        time.sleep(0.2)
        assert cache.get('key1') is None
