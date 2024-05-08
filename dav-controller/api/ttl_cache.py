from typing import Any
from cachetools import TTLCache

# TTLCacheManager: Manages a temporary in-memory cache with automatic eviction based on time-to-live.
# For production multi-pod deployments, use Redis for shared caching.

class TTLCacheManager:
    def __init__(self, maxsize: int = 100, ttl_seconds: int = 3600):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def set(self, key: str, value: Any):
        self._cache[key] = value

    def get(self, key: str) -> Any:
        return self._cache.get(key)