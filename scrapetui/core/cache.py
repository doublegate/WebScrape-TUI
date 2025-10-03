"""Caching layer for performance optimization."""

from typing import Any, Optional, Callable, Dict
from functools import wraps
import json
import time
from threading import Lock

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..config import get_config
from ..utils.logging import get_logger

# Lazy initialization - do not create logger/config at module level
# to avoid import-time side effects that can cause test hangs


class Cache:
    """Abstract cache interface."""

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache with TTL (seconds).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 3600)
        """
        raise NotImplementedError

    def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        raise NotImplementedError

    def clear(self):
        """Clear all cached values."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        return self.get(key) is not None


class MemoryCache(Cache):
    """Thread-safe in-memory cache implementation."""

    def __init__(self):
        """Initialize memory cache."""
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            # Check expiration
            if key in self._expiry and time.time() > self._expiry[key]:
                # Delete inline to avoid nested lock acquisition
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
                return None

            return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self._lock:
            self._cache[key] = value
            self._expiry[key] = time.time() + ttl

    def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)

    def clear(self):
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()

    def stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            expired = sum(1 for exp in self._expiry.values() if time.time() > exp)
            return {
                'total_keys': len(self._cache),
                'expired_keys': expired,
                'active_keys': len(self._cache) - expired
            }


class RedisCache(Cache):
    """Redis cache implementation."""

    def __init__(self):
        """Initialize Redis cache."""
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package not installed. Install with: pip install redis"
            )

        # Lazy initialization - get config and logger when needed
        config = get_config()
        logger = get_logger(__name__)

        try:
            self.client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=config.redis_db,
                password=config.redis_password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {config.redis_host}:{config.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Redis SET error: {e}")

    def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        try:
            self.client.delete(key)
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Redis DELETE error: {e}")

    def clear(self):
        """Clear all cached values."""
        try:
            self.client.flushdb()
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Redis CLEAR error: {e}")


# Global cache instance
_cache_instance: Optional[Cache] = None
_cache_lock = Lock()


def get_cache() -> Cache:
    """
    Get global cache instance (singleton).

    Returns:
        Cache instance (MemoryCache or RedisCache)
    """
    global _cache_instance

    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:  # Double-check locking
                # Lazy initialization - get config and logger only when creating cache
                config = get_config()
                logger = get_logger(__name__)

                if not config.cache_enabled:
                    logger.info("Caching disabled, using MemoryCache")
                    _cache_instance = MemoryCache()
                elif config.cache_type == 'redis' and REDIS_AVAILABLE:
                    try:
                        _cache_instance = RedisCache()
                        logger.info("Using RedisCache")
                    except Exception as e:
                        logger.warning(
                            f"Failed to initialize Redis cache: {e}, "
                            "falling back to MemoryCache"
                        )
                        _cache_instance = MemoryCache()
                else:
                    _cache_instance = MemoryCache()
                    logger.info("Using MemoryCache")

    return _cache_instance


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 3600)
        key_prefix: Prefix for cache key (default: function name)

    Returns:
        Decorator function

    Example:
        >>> @cached(ttl=300, key_prefix='user')
        ... def get_user(user_id):
        ...     return fetch_user_from_db(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Check cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger = get_logger(__name__)
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Execute function
            logger = get_logger(__name__)
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        wrapper.cache_clear = lambda: get_cache().clear()
        return wrapper
    return decorator


def invalidate_cache(pattern: str = None):
    """
    Invalidate cache entries matching pattern.

    Args:
        pattern: Cache key pattern (None = clear all)

    Note:
        For MemoryCache, this clears all entries.
        For RedisCache with pattern support, could use SCAN.
    """
    cache = get_cache()
    logger = get_logger(__name__)
    if pattern is None:
        cache.clear()
        logger.info("Cache cleared")
    else:
        # Simple implementation: clear all for now
        # TODO: Implement pattern-based clearing for Redis
        cache.clear()
        logger.info(f"Cache cleared (pattern: {pattern})")
