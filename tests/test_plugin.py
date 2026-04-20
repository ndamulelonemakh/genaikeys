"""Tests for the SecretManagerPlugin abstract interface."""

from unittest.mock import patch

import pytest

from genaikeys import SecretManagerPlugin
from genaikeys.plugins import available_backends, load_backend


class TestPluginInterface:
    """Verify the contract of SecretManagerPlugin."""

    def test_cannot_instantiate_abstract_class(self):
        """SecretManagerPlugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SecretManagerPlugin()

    def test_subclass_must_implement_get_secret(self):
        """A subclass without get_secret cannot be instantiated."""

        class Incomplete(SecretManagerPlugin):
            pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_minimal_subclass_works(self):
        """A subclass with only get_secret can be instantiated and used."""

        class Minimal(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                return f"value-of-{secret_name}"

        plugin = Minimal()
        assert plugin.get_secret("FOO") == "value-of-FOO"

    def test_exists_default_raises_not_implemented(self):
        """The default exists() raises NotImplementedError."""

        class Minimal(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                return "x"

        with pytest.raises(NotImplementedError):
            Minimal().exists("key")

    def test_list_secrets_default_raises_not_implemented(self):
        """The default list_secrets() raises NotImplementedError."""

        class Minimal(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                return "x"

        with pytest.raises(NotImplementedError):
            Minimal().list_secrets()

    def test_full_implementation(self):
        """A subclass implementing all three methods works correctly."""

        class FullPlugin(SecretManagerPlugin):
            def __init__(self):
                self._store = {"A": "1", "B": "2"}

            def get_secret(self, secret_name: str) -> str:
                return self._store[secret_name]

            def exists(self, secret_name: str, **kwargs) -> bool:
                return secret_name in self._store

            def list_secrets(self, max_results: int = 100) -> list[str]:
                return list(self._store.keys())[:max_results]

        plugin = FullPlugin()
        assert plugin.get_secret("A") == "1"
        assert plugin.exists("A") is True
        assert plugin.exists("C") is False
        assert plugin.list_secrets() == ["A", "B"]
        assert plugin.list_secrets(max_results=1) == ["A"]

    def test_get_secret_missing_key_can_raise(self):
        """Plugin implementations are free to raise KeyError for missing secrets."""

        class StrictPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                raise KeyError(f"No such secret: {secret_name}")

        with pytest.raises(KeyError, match="No such secret"):
            StrictPlugin().get_secret("MISSING")

    def test_plugins_package_re_exports_base_interface(self):
        assert SecretManagerPlugin is load_backend.__globals__["SecretManagerPlugin"]

    def test_available_backends_lists_entry_points(self):
        mock_entry_point = type("EntryPoint", (), {"name": "demo"})()

        with patch("genaikeys.plugins.registry.entry_points", return_value=[mock_entry_point]):
            assert available_backends() == ["demo"]

    def test_load_backend_resolves_registered_backend(self):
        class DemoPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                return secret_name

        class EntryPoint:
            name = "demo"

            @staticmethod
            def load():
                return DemoPlugin

        with patch("genaikeys.plugins.registry.entry_points", return_value=[EntryPoint()]):
            assert load_backend("demo") is DemoPlugin
