import asyncio
import logging
import threading
import time
from typing import Any

from .plugins.base import SecretManagerPlugin

logger = logging.getLogger(__name__)


class InMemorySecretManager:
    __slots__ = ("_cache", "_cache_lock", "_cache_duration", "_plugin")

    def __init__(self, plugin: SecretManagerPlugin, cache_duration: int = 3600):
        self._cache_lock = threading.Lock()
        self._plugin = plugin
        self._cache_duration = cache_duration
        self._cache: dict[str, dict[str, Any]] = {}

    def get_secret(self, secret_name: str) -> str:
        with self._cache_lock:
            current_time = time.time()

            if secret_name in self._cache:
                cached_secret = self._cache[secret_name]
                age = current_time - cached_secret["timestamp"]
                if age < self._cache_duration:
                    logger.debug("cache hit for %r (age=%.1fs)", secret_name, age)
                    return str(cached_secret["value"])
                logger.debug("cache expired for %r (age=%.1fs)", secret_name, age)
            else:
                logger.debug("cache miss for %r", secret_name)

            try:
                secret_value: str = self._plugin.get_secret(secret_name)
            except Exception as exc:
                logger.warning(
                    "backend %s failed to fetch %r: %s",
                    type(self._plugin).__name__,
                    secret_name,
                    type(exc).__name__,
                )
                raise
            self._cache[secret_name] = {"value": secret_value, "timestamp": current_time}
            logger.info("loaded %r from %s", secret_name, type(self._plugin).__name__)
            return secret_value

    def invalidate_cache(self, secret_name: str | None = None) -> None:
        with self._cache_lock:
            if secret_name is None:
                logger.info("clearing cache (%d entries)", len(self._cache))
                self._cache.clear()
            elif secret_name in self._cache:
                logger.debug("invalidating cache entry %r", secret_name)
                del self._cache[secret_name]

    async def aget_secret(self, secret_name: str) -> str:
        return await asyncio.to_thread(self.get_secret, secret_name)

    def __repr__(self) -> str:
        return f"<InMemorySecretManager backend={type(self._plugin).__name__} entries=redacted>"

    def __reduce__(self):
        raise TypeError("InMemorySecretManager is not picklable: refusing to serialize cached secrets")

    def __copy__(self):
        raise TypeError("InMemorySecretManager is not copyable: refusing to duplicate cached secrets")

    def __deepcopy__(self, memo):
        raise TypeError("InMemorySecretManager is not copyable: refusing to duplicate cached secrets")
