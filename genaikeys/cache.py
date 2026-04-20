import logging
import os
import threading
import time
from typing import Any

from .plugins.base import SecretManagerPlugin

logger = logging.getLogger(__name__)


class InMemorySecretManager:
    def __init__(self, plugin: SecretManagerPlugin, cache_duration: int = 3600):
        self._cache_lock = threading.Lock()
        self.plugin = plugin
        self.cache_duration = cache_duration
        self.cache: dict[str, dict[str, Any]] = {}

    def get_secret(self, secret_name: str) -> str:
        with self._cache_lock:
            current_time = time.time()

            if secret_name in self.cache:
                cached_secret = self.cache[secret_name]
                age = current_time - cached_secret["timestamp"]
                if age < self.cache_duration:
                    logger.debug("cache hit for %r (age=%.1fs)", secret_name, age)
                    return str(cached_secret["value"])
                logger.debug("cache expired for %r (age=%.1fs)", secret_name, age)
            else:
                logger.debug("cache miss for %r", secret_name)

            try:
                secret_value: str = self.plugin.get_secret(secret_name)
            except Exception as exc:
                logger.warning(
                    "backend %s failed to fetch %r: %s",
                    type(self.plugin).__name__,
                    secret_name,
                    exc,
                )
                raise
            self.cache[secret_name] = {"value": secret_value, "timestamp": current_time}
            logger.info("loaded %r from %s", secret_name, type(self.plugin).__name__)
            return secret_value

    def invalidate_cache(self, secret_name: str | None = None) -> None:
        with self._cache_lock:
            if secret_name is None:
                logger.info("clearing cache (%d entries)", len(self.cache))
                self.cache.clear()
            elif secret_name in self.cache:
                logger.debug("invalidating cache entry %r", secret_name)
                del self.cache[secret_name]
                if secret_name in os.environ:
                    del os.environ[secret_name]
