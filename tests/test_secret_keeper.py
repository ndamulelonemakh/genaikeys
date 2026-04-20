"""Unit tests for SecretKeeper core functionality."""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from genaikeys import SecretKeeper, SecretManagerPlugin
from genaikeys._secret_manager_default import InMemorySecretManager
from genaikeys._settings import AWSSettings, AzureKeyVaultSettings, GCPSettings


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _FakePlugin(SecretManagerPlugin):
    """In-process plugin that returns configurable secrets."""

    def __init__(self, secrets: dict | None = None):
        self._secrets = secrets or {}
        self.call_count = 0

    def get_secret(self, secret_name: str) -> str:
        self.call_count += 1
        if secret_name not in self._secrets:
            raise KeyError(f"Secret '{secret_name}' not found")
        return self._secrets[secret_name]

    def exists(self, secret_name: str, **kwargs) -> bool:
        return secret_name in self._secrets

    def list_secrets(self, max_results: int = 100) -> list[str]:
        return list(self._secrets.keys())[:max_results]


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the SecretKeeper singleton between tests."""
    from genaikeys import SingletonMeta
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()


# ---------------------------------------------------------------------------
# Pydantic settings tests
# ---------------------------------------------------------------------------

class TestAzureKeyVaultSettings:
    def test_reads_from_env(self):
        with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://vault.azure.net/"}):
            cfg = AzureKeyVaultSettings()
        assert cfg.azure_key_vault_url == "https://vault.azure.net/"
        assert cfg.managed_identity_client_id is None
        assert cfg.secretkeeper_debug is False

    def test_constructor_override_takes_precedence(self):
        with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://env-vault.azure.net/"}):
            cfg = AzureKeyVaultSettings(azure_key_vault_url="https://override.azure.net/")
        assert cfg.azure_key_vault_url == "https://override.azure.net/"

    def test_optional_fields(self):
        with patch.dict("os.environ", {
            "AZURE_KEY_VAULT_URL": "https://vault.azure.net/",
            "MANAGED_IDENTITY_CLIENT_ID": "my-client-id",
            "SECRETKEEPER_DEBUG": "1",
        }):
            cfg = AzureKeyVaultSettings()
        assert cfg.managed_identity_client_id == "my-client-id"
        assert cfg.secretkeeper_debug is True

    def test_raises_when_url_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                AzureKeyVaultSettings()
        assert "azure_key_vault_url" in str(exc_info.value)

    def test_extra_env_vars_ignored(self):
        with patch.dict("os.environ", {
            "AZURE_KEY_VAULT_URL": "https://vault.azure.net/",
            "SOME_RANDOM_VAR": "noise",
        }):
            cfg = AzureKeyVaultSettings()  # should not raise
        assert cfg.azure_key_vault_url == "https://vault.azure.net/"


class TestAWSSettings:
    def test_reads_from_env(self):
        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
            cfg = AWSSettings()
        assert cfg.aws_default_region == "eu-west-1"

    def test_constructor_override_takes_precedence(self):
        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            cfg = AWSSettings(aws_default_region="ap-southeast-1")
        assert cfg.aws_default_region == "ap-southeast-1"

    def test_raises_when_region_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                AWSSettings()
        assert "aws_default_region" in str(exc_info.value)

    def test_profile_defaults_to_none(self):
        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
            cfg = AWSSettings()
        assert cfg.aws_profile is None

    def test_profile_reads_from_env(self):
        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1", "AWS_PROFILE": "my-sso"}):
            cfg = AWSSettings()
        assert cfg.aws_profile == "my-sso"

    def test_profile_constructor_override(self):
        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1", "AWS_PROFILE": "env-profile"}):
            cfg = AWSSettings(aws_profile="override-profile")
        assert cfg.aws_profile == "override-profile"


class TestGCPSettings:
    def test_reads_from_env(self):
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "my-project"}):
            cfg = GCPSettings()
        assert cfg.google_cloud_project == "my-project"

    def test_constructor_override_takes_precedence(self):
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "env-project"}):
            cfg = GCPSettings(google_cloud_project="override-project")
        assert cfg.google_cloud_project == "override-project"

    def test_raises_when_project_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                GCPSettings()
        assert "google_cloud_project" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AzureKeyVaultPlugin – name normalisation
# ---------------------------------------------------------------------------

class TestAzureKeyVaultPlugin:
    def test_exists_normalises_underscores_to_dashes(self, mock_cloud_backends):
        """exists('MY_SECRET') must match 'my-secret' returned by list_secrets."""
        import genaikeys._azure_keyvault as _az
        mock_client = MagicMock()
        # list_properties_of_secrets returns names with dashes (Azure KV format)
        mock_secret = MagicMock()
        mock_secret.name = "my-secret"
        mock_client.list_properties_of_secrets.return_value = [mock_secret]

        with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://vault.azure.net/"}):
            plugin = _az.AzureKeyVaultPlugin()
        plugin.client = mock_client

        assert plugin.exists("my_secret") is True   # underscore input → dash lookup
        assert plugin.exists("my-secret") is True   # dash input → dash lookup (unchanged)
        assert plugin.exists("OTHER_SECRET") is False


# ---------------------------------------------------------------------------
# AWSSecretsManagerPlugin – boto3.Session wiring
# ---------------------------------------------------------------------------

class TestAWSSecretsManagerPlugin:
    def test_session_created_without_profile(self, mock_cloud_backends):
        """Without a profile, Session is created with profile_name=None."""
        import genaikeys._aws_secret_manager as _aws
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        with patch.object(_aws.boto3, "Session", return_value=mock_session) as MockSession:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
                _aws.AWSSecretsManagerPlugin(region_name="eu-west-1")
            MockSession.assert_called_once_with(profile_name=None, region_name="eu-west-1")
            mock_session.client.assert_called_once_with("secretsmanager")

    def test_session_created_with_profile(self, mock_cloud_backends):
        """With a profile, Session is created with the given profile_name (SSO support)."""
        import genaikeys._aws_secret_manager as _aws
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        with patch.object(_aws.boto3, "Session", return_value=mock_session) as MockSession:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
                _aws.AWSSecretsManagerPlugin(region_name="eu-west-1", profile_name="my-sso")
            MockSession.assert_called_once_with(profile_name="my-sso", region_name="eu-west-1")

    def test_profile_from_env_var(self, mock_cloud_backends):
        """AWS_PROFILE env var is picked up via AWSSettings.aws_profile."""
        import genaikeys._aws_secret_manager as _aws
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        with patch.object(_aws.boto3, "Session", return_value=mock_session) as MockSession:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1", "AWS_PROFILE": "sso-dev"}):
                _aws.AWSSecretsManagerPlugin(region_name="eu-west-1")
            MockSession.assert_called_once_with(profile_name="sso-dev", region_name="eu-west-1")


# ---------------------------------------------------------------------------
# InMemorySecretManager tests
# ---------------------------------------------------------------------------

class TestInMemorySecretManager:
    def test_get_secret_returns_value(self):
        plugin = _FakePlugin({"MY_KEY": "secret-value"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        assert mgr.get_secret("MY_KEY") == "secret-value"

    def test_caches_on_second_call(self):
        plugin = _FakePlugin({"MY_KEY": "secret-value"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        mgr.get_secret("MY_KEY")
        mgr.get_secret("MY_KEY")
        assert plugin.call_count == 1

    def test_cache_expires(self):
        plugin = _FakePlugin({"MY_KEY": "secret-value"})
        mgr = InMemorySecretManager(plugin, cache_duration=0)
        mgr.get_secret("MY_KEY")
        time.sleep(0.01)
        mgr.get_secret("MY_KEY")
        assert plugin.call_count == 2

    def test_invalidate_specific_key(self):
        plugin = _FakePlugin({"A": "1", "B": "2"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        mgr.get_secret("A")
        mgr.get_secret("B")
        mgr.invalidate_cache("A")
        mgr.get_secret("A")
        mgr.get_secret("B")
        # A was fetched again; B was served from cache
        assert plugin.call_count == 3

    def test_invalidate_all_keys(self):
        plugin = _FakePlugin({"A": "1", "B": "2"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        mgr.get_secret("A")
        mgr.get_secret("B")
        mgr.invalidate_cache()
        mgr.get_secret("A")
        mgr.get_secret("B")
        assert plugin.call_count == 4

    def test_thread_safety(self):
        """Multiple threads should not corrupt the cache."""
        plugin = _FakePlugin({"K": "v"})
        mgr = InMemorySecretManager(plugin, cache_duration=60)
        errors = []

        def worker():
            try:
                for _ in range(50):
                    mgr.get_secret("K")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert mgr.get_secret("K") == "v"


# ---------------------------------------------------------------------------
# SecretKeeper tests
# ---------------------------------------------------------------------------

class TestSecretKeeper:
    def test_get_returns_secret(self):
        plugin = _FakePlugin({"MY_SECRET": "abc123"})
        sk = SecretKeeper(plugin)
        assert sk.get("MY_SECRET") == "abc123"

    def test_get_secret_alias(self):
        plugin = _FakePlugin({"MY_SECRET": "abc123"})
        sk = SecretKeeper(plugin)
        assert sk.get_secret("MY_SECRET") == "abc123"

    def test_get_does_not_store_in_environ(self):
        import os
        plugin = _FakePlugin({"MY_SECRET": "abc123"})
        sk = SecretKeeper(plugin)
        sk.get("MY_SECRET")
        assert "MY_SECRET" not in os.environ

    def test_singleton_returns_same_instance(self):
        plugin = _FakePlugin({"K": "v"})
        sk1 = SecretKeeper(plugin)
        sk2 = SecretKeeper(plugin)
        assert sk1 is sk2

    def test_clear_specific_key(self):
        plugin = _FakePlugin({"K": "v"})
        sk = SecretKeeper(plugin)
        sk.get("K")
        sk.clear("K")
        sk.get("K")
        assert plugin.call_count == 2

    def test_clear_all(self):
        plugin = _FakePlugin({"A": "1", "B": "2"})
        sk = SecretKeeper(plugin)
        sk.get("A")
        sk.get("B")
        sk.clear()
        sk.get("A")
        sk.get("B")
        assert plugin.call_count == 4

    def test_get_openai_key(self):
        plugin = _FakePlugin({"OPENAI_API_KEY": "sk-openai"})
        sk = SecretKeeper(plugin)
        assert sk.get_openai_key() == "sk-openai"

    def test_get_anthropic_key(self):
        plugin = _FakePlugin({"ANTHROPIC_API_KEY": "sk-ant"})
        sk = SecretKeeper(plugin)
        assert sk.get_anthropic_key() == "sk-ant"

    def test_get_gemini_key(self):
        plugin = _FakePlugin({"GEMINI_API_KEY": "ai-gemini"})
        sk = SecretKeeper(plugin)
        assert sk.get_gemini_key() == "ai-gemini"

    def test_missing_secret_raises(self):
        plugin = _FakePlugin({})
        sk = SecretKeeper(plugin)
        with pytest.raises(KeyError):
            sk.get("DOES_NOT_EXIST")


# ---------------------------------------------------------------------------
# SecretManagerPlugin base class tests
# ---------------------------------------------------------------------------

class TestSecretManagerPlugin:
    def test_exists_raises_not_implemented(self):
        class Minimal(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                return "x"

        m = Minimal()
        with pytest.raises(NotImplementedError):
            m.exists("k")

    def test_list_secrets_raises_not_implemented(self):
        class Minimal(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                return "x"

        m = Minimal()
        with pytest.raises(NotImplementedError):
            m.list_secrets()


# ---------------------------------------------------------------------------
# SecretKeeper factory methods
#
# All tests use the ``mock_cloud_backends`` fixture (conftest.py) which stubs
# the cloud SDK packages in sys.modules so the backend modules can be imported
# without the real azure / boto3 / google packages being installed.
#
# For "raises" tests the real AzureKeyVaultPlugin constructor runs; pydantic
# raises ValidationError before any cloud SDK call is made.
#
# For "creates plugin" tests we pre-import the backend module (which loads
# cleanly under stubbed SDKs) and then use patch.object so the factory picks
# up the mock via its lazy ``from ._xxx import Plugin`` import.
# ---------------------------------------------------------------------------

class TestSecretKeeperFactories:
    # --- missing config → ValidationError ---

    def test_azure_factory_raises_without_url(self, mock_cloud_backends):
        """Missing AZURE_KEY_VAULT_URL → pydantic ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            with patch.dict("os.environ", {}, clear=True):
                SecretKeeper.azure(vault_url=None)
        assert "azure_key_vault_url" in str(exc_info.value)

    def test_aws_factory_raises_without_region(self, mock_cloud_backends):
        """Missing AWS_DEFAULT_REGION → pydantic ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            with patch.dict("os.environ", {}, clear=True):
                SecretKeeper.aws(region_name=None)
        assert "aws_default_region" in str(exc_info.value)

    def test_gcp_factory_raises_without_project(self, mock_cloud_backends):
        """Missing GOOGLE_CLOUD_PROJECT → pydantic ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            with patch.dict("os.environ", {}, clear=True):
                SecretKeeper.gcp(project_id=None)
        assert "google_cloud_project" in str(exc_info.value)

    # --- factory plumbing: correct kwargs reach the plugin ---

    def test_azure_factory_with_explicit_url(self, mock_cloud_backends):
        """Explicit vault_url is forwarded to AzureKeyVaultPlugin unchanged."""
        import genaikeys._azure_keyvault as _az
        mock_plugin = MagicMock()
        with patch.object(_az, "AzureKeyVaultPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {}, clear=True):
                SecretKeeper.azure(vault_url="https://my-vault.vault.azure.net/")
            MockPlugin.assert_called_once_with(vault_url="https://my-vault.vault.azure.net/")

    def test_azure_factory_passes_none_when_url_omitted(self, mock_cloud_backends):
        """When vault_url is omitted the factory passes None; pydantic reads the env var."""
        import genaikeys._azure_keyvault as _az
        mock_plugin = MagicMock()
        with patch.object(_az, "AzureKeyVaultPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://my-vault.vault.azure.net/"}):
                SecretKeeper.azure()
            MockPlugin.assert_called_once_with(vault_url=None)

    def test_aws_factory_with_explicit_region(self, mock_cloud_backends):
        """Explicit region_name is forwarded to AWSSecretsManagerPlugin unchanged."""
        import genaikeys._aws_secret_manager as _aws
        mock_plugin = MagicMock()
        with patch.object(_aws, "AWSSecretsManagerPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {}, clear=True):
                SecretKeeper.aws(region_name="eu-west-1")
            MockPlugin.assert_called_once_with(region_name="eu-west-1", profile_name=None)

    def test_aws_factory_passes_none_when_region_omitted(self, mock_cloud_backends):
        """When region_name is omitted the factory passes None; pydantic reads the env var."""
        import genaikeys._aws_secret_manager as _aws
        mock_plugin = MagicMock()
        with patch.object(_aws, "AWSSecretsManagerPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
                SecretKeeper.aws()
            MockPlugin.assert_called_once_with(region_name=None, profile_name=None)

    def test_aws_factory_with_profile_name(self, mock_cloud_backends):
        """profile_name is forwarded to AWSSecretsManagerPlugin for SSO support."""
        import genaikeys._aws_secret_manager as _aws
        mock_plugin = MagicMock()
        with patch.object(_aws, "AWSSecretsManagerPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
                SecretKeeper.aws(profile_name="my-sso-profile")
            MockPlugin.assert_called_once_with(region_name=None, profile_name="my-sso-profile")

    def test_gcp_factory_with_explicit_project(self, mock_cloud_backends):
        """Explicit project_id is forwarded to GCPSecretManagerPlugin unchanged."""
        import genaikeys._gcp_secret_manager as _gcp
        mock_plugin = MagicMock()
        with patch.object(_gcp, "GCPSecretManagerPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {}, clear=True):
                SecretKeeper.gcp(project_id="my-project")
            MockPlugin.assert_called_once_with(project_id="my-project")

    def test_gcp_factory_passes_none_when_project_omitted(self, mock_cloud_backends):
        """When project_id is omitted the factory passes None; pydantic reads the env var."""
        import genaikeys._gcp_secret_manager as _gcp
        mock_plugin = MagicMock()
        with patch.object(_gcp, "GCPSecretManagerPlugin", return_value=mock_plugin) as MockPlugin:
            with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "env-project"}):
                SecretKeeper.gcp()
            MockPlugin.assert_called_once_with(project_id=None)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Verify graceful behaviour when the underlying plugin raises errors."""

    def test_plugin_runtime_error_propagates(self):
        """A RuntimeError from the plugin is not swallowed."""

        class FailingPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                raise RuntimeError("Network unreachable")

        sk = SecretKeeper(FailingPlugin())
        with pytest.raises(RuntimeError, match="Network unreachable"):
            sk.get("ANY_KEY")

    def test_plugin_permission_error_propagates(self):
        """A PermissionError (e.g. 403) from the plugin is surfaced."""

        class ForbiddenPlugin(SecretManagerPlugin):
            def get_secret(self, secret_name: str) -> str:
                raise PermissionError("Access denied: 403 Forbidden")

        sk = SecretKeeper(ForbiddenPlugin())
        with pytest.raises(PermissionError, match="403"):
            sk.get("ANY_KEY")

    def test_cache_does_not_cache_errors(self):
        """If get_secret raises, the error is NOT cached — next call retries."""
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
        # Second call should succeed (error was not cached)
        assert mgr.get_secret("K") == "recovered-value"
        assert call_count == 2

    def test_cache_ttl_forces_refetch(self):
        """After TTL expires, the plugin is called again even for a cached key."""
        plugin = _FakePlugin({"K": "v"})
        mgr = InMemorySecretManager(plugin, cache_duration=0)
        mgr.get_secret("K")
        time.sleep(0.01)
        mgr.get_secret("K")
        assert plugin.call_count == 2
