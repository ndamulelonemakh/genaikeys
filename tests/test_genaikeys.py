import copy
import os
import pickle

import pytest

from genaikeys import GenAIKeys, SecretManagerPlugin
from tests.helpers import FakePlugin


class TestGenAIKeys:
    def test_get_returns_secret(self):
        plugin = FakePlugin({"MY_SECRET": "abc123"})
        sk = GenAIKeys(plugin)
        assert sk.get("MY_SECRET") == "abc123"

    def test_get_secret_alias(self):
        plugin = FakePlugin({"MY_SECRET": "abc123"})
        sk = GenAIKeys(plugin)
        assert sk.get_secret("MY_SECRET") == "abc123"

    def test_get_does_not_store_in_environ(self):
        plugin = FakePlugin({"MY_SECRET": "abc123"})
        sk = GenAIKeys(plugin)
        sk.get("MY_SECRET")
        assert "MY_SECRET" not in os.environ

    def test_singleton_returns_same_instance(self):
        plugin = FakePlugin({"K": "v"})
        sk1 = GenAIKeys(plugin)
        sk2 = GenAIKeys(plugin)
        assert sk1 is sk2

    def test_clear_specific_key(self):
        plugin = FakePlugin({"K": "v"})
        sk = GenAIKeys(plugin)
        sk.get("K")
        sk.clear("K")
        sk.get("K")
        assert plugin.call_count == 2

    def test_clear_all(self):
        plugin = FakePlugin({"A": "1", "B": "2"})
        sk = GenAIKeys(plugin)
        sk.get("A")
        sk.get("B")
        sk.clear()
        sk.get("A")
        sk.get("B")
        assert plugin.call_count == 4

    def test_get_openai_key(self):
        plugin = FakePlugin({"OPENAI_API_KEY": "sk-openai"})
        sk = GenAIKeys(plugin)
        assert sk.get_openai_key() == "sk-openai"

    def test_get_anthropic_key(self):
        plugin = FakePlugin({"ANTHROPIC_API_KEY": "sk-ant"})
        sk = GenAIKeys(plugin)
        assert sk.get_anthropic_key() == "sk-ant"

    def test_get_gemini_key(self):
        plugin = FakePlugin({"GEMINI_API_KEY": "ai-gemini"})
        sk = GenAIKeys(plugin)
        assert sk.get_gemini_key() == "ai-gemini"

    def test_missing_secret_raises(self):
        plugin = FakePlugin({})
        sk = GenAIKeys(plugin)
        with pytest.raises(KeyError):
            sk.get("DOES_NOT_EXIST")

    def test_attribute_access_returns_secret(self):
        plugin = FakePlugin({"OPENAI_KEY": "sk-attr"})
        sk = GenAIKeys(plugin)
        assert sk.OPENAI_KEY == "sk-attr"

    def test_attribute_access_missing_raises_attribute_error(self):
        plugin = FakePlugin({})
        sk = GenAIKeys(plugin)
        with pytest.raises(AttributeError):
            _ = sk.NOPE

    def test_hasattr_does_not_raise(self):
        plugin = FakePlugin({})
        sk = GenAIKeys(plugin)
        assert hasattr(sk, "MISSING") is False

    def test_attribute_access_rejects_non_uppercase(self):
        plugin = FakePlugin({"lowercase_key": "should-not-be-fetched"})
        sk = GenAIKeys(plugin)
        with pytest.raises(AttributeError):
            _ = sk.lowercase_key
        assert plugin.call_count == 0

    def test_dunder_attribute_does_not_hit_backend(self):
        plugin = FakePlugin({})
        sk = GenAIKeys(plugin)
        with pytest.raises(AttributeError):
            _ = sk.__some_private__
        assert plugin.call_count == 0

    def test_item_access_returns_secret(self):
        plugin = FakePlugin({"FOO": "bar"})
        sk = GenAIKeys(plugin)
        assert sk["FOO"] == "bar"

    def test_contains(self):
        plugin = FakePlugin({"FOO": "bar"})
        sk = GenAIKeys(plugin)
        assert "FOO" in sk
        assert "MISSING" not in sk

    def test_pickle_refused(self):
        plugin = FakePlugin({"FOO": "bar"})
        sk = GenAIKeys(plugin)
        sk.get("FOO")
        with pytest.raises(TypeError):
            pickle.dumps(sk)

    def test_deepcopy_refused(self):
        plugin = FakePlugin({"FOO": "bar"})
        sk = GenAIKeys(plugin)
        sk.get("FOO")
        with pytest.raises(TypeError):
            copy.deepcopy(sk)
        with pytest.raises(TypeError):
            copy.copy(sk)

    def test_repr_does_not_leak_state(self):
        plugin = FakePlugin({"FOO": "super-secret"})
        sk = GenAIKeys(plugin)
        sk.get("FOO")
        assert "super-secret" not in repr(sk)
        assert "FOO" not in repr(sk)

    def test_manager_repr_does_not_leak(self):
        plugin = FakePlugin({"FOO": "super-secret"})
        sk = GenAIKeys(plugin)
        sk.get("FOO")
        assert "super-secret" not in repr(sk._manager)
        assert "FOO" not in repr(sk._manager)

    def test_manager_state_is_private(self):
        plugin = FakePlugin({"FOO": "bar"})
        sk = GenAIKeys(plugin)
        sk.get("FOO")
        assert not hasattr(sk._manager, "cache")
        assert not hasattr(sk._manager, "plugin")

    def test_plugin_runtime_error_propagates(self):
        class FailingPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                raise RuntimeError("Network unreachable")

        sk = GenAIKeys(FailingPlugin())
        with pytest.raises(RuntimeError, match="Network unreachable"):
            sk.get("ANY_KEY")

    def test_plugin_permission_error_propagates(self):
        class ForbiddenPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                raise PermissionError("Access denied: 403 Forbidden")

        sk = GenAIKeys(ForbiddenPlugin())
        with pytest.raises(PermissionError, match="403"):
            sk.get("ANY_KEY")
