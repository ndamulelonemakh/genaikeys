"""
A simple version of SecretManager that only caches secrets in process memory.
"""

import logging
import os
import threading
import time
from typing import Any

from .types import SecretManagerPlugin

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
                if current_time - cached_secret["timestamp"] < self.cache_duration:
                    return cached_secret["value"]

            secret_value = self.plugin.get_secret(secret_name)
            self.cache[secret_name] = {
                "value": secret_value,
                "timestamp": current_time
            }
            return secret_value

    def invalidate_cache(self, secret_name: str | None = None) -> None:
        with self._cache_lock:
            if secret_name is None:
                self.cache.clear()
            elif secret_name in self.cache:
                del self.cache[secret_name]
                if secret_name in os.environ:
                    del os.environ[secret_name]
