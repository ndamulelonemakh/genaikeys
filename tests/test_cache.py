import threading
import time

import pytest

from genaikeys import SecretManagerPlugin
from genaikeys.cache import InMemorySecretManager
from tests.helpers import FakePlugin


class TestInMemorySecretManager:
    def test_get_secret_returns_value(self):
        plugin = FakePlugin({"MY_KEY": "secret-value"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        assert mgr.get_secret("MY_KEY") == "secret-value"

    def test_caches_on_second_call(self):
        plugin = FakePlugin({"MY_KEY": "secret-value"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        mgr.get_secret("MY_KEY")
        mgr.get_secret("MY_KEY")
        assert plugin.call_count == 1

    def test_cache_expires(self):
        plugin = FakePlugin({"MY_KEY": "secret-value"})
        mgr = InMemorySecretManager(plugin, cache_duration=0)
        mgr.get_secret("MY_KEY")
        time.sleep(0.01)
        mgr.get_secret("MY_KEY")
        assert plugin.call_count == 2

    def test_invalidate_specific_key(self):
        plugin = FakePlugin({"A": "1", "B": "2"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        mgr.get_secret("A")
        mgr.get_secret("B")
        mgr.invalidate_cache("A")
        mgr.get_secret("A")
        mgr.get_secret("B")
        assert plugin.call_count == 3

    def test_invalidate_all_keys(self):
        plugin = FakePlugin({"A": "1", "B": "2"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        mgr.get_secret("A")
        mgr.get_secret("B")
        mgr.invalidate_cache()
        mgr.get_secret("A")
        mgr.get_secret("B")
        assert plugin.call_count == 4

    def test_thread_safety(self):
        plugin = FakePlugin({"K": "v"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        errors = []

        def worker():
            try:
                for _ in range(50):
                    mgr.get_secret("K")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors
        assert mgr.get_secret("K") == "v"

    def test_cache_does_not_cache_errors(self):
        call_count = 0

        class FlakeyPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ConnectionError("Temporary failure")
                return "recovered-value"

        mgr = InMemorySecretManager(FlakeyPlugin(), cache_duration=60)
        with pytest.raises(ConnectionError):
            mgr.get_secret("K")
        assert mgr.get_secret("K") == "recovered-value"
        assert call_count == 2
