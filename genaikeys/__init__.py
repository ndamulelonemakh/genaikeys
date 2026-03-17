import threading
from typing import Optional

from ._secret_manager_default import InMemorySecretManager
from .types import SecretManagerPlugin


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SecretKeeper(metaclass=SingletonMeta):
    def __init__(self, plugin: SecretManagerPlugin, cache_duration: int = 3600):
        self._manager = InMemorySecretManager(plugin, cache_duration)

    @classmethod
    def from_defaults(cls, cache_duration: int = 3600, vault_url: Optional[str] = None):
        """Create a SecretKeeper backed by Azure Key Vault (default backend)."""
        from ._azure_keyvault import AzureKeyVaultPlugin
        return cls(AzureKeyVaultPlugin(vault_url=vault_url), cache_duration)

    @classmethod
    def azure(cls, cache_duration: int = 3600, vault_url: Optional[str] = None):
        """Create a SecretKeeper backed by Azure Key Vault."""
        return cls.from_defaults(cache_duration, vault_url)

    @classmethod
    def aws(cls, cache_duration: int = 3600, region_name: Optional[str] = None):
        """Create a SecretKeeper backed by AWS Secrets Manager."""
        from ._aws_secret_manager import AWSSecretsManagerPlugin
        return cls(AWSSecretsManagerPlugin(region_name=region_name), cache_duration)

    @classmethod
    def gcp(cls, cache_duration: int = 3600, project_id: Optional[str] = None):
        """Create a SecretKeeper backed by Google Secret Manager."""
        from ._gcp_secret_manager import GCPSecretManagerPlugin
        return cls(GCPSecretManagerPlugin(project_id=project_id), cache_duration)

    def get_secret(self, secret_name: str) -> str:
        return self._manager.get_secret(secret_name)

    def get(self, secret_name: str) -> str:
        return self.get_secret(secret_name)

    def clear(self, secret_name: str | None = None):
        self._manager.invalidate_cache(secret_name=secret_name)

    # region Popular Gen AI providers
    def get_openai_key(self) -> str:
        return self.get("OPENAI_API_KEY")

    def get_anthropic_key(self) -> str:
        return self.get("ANTHROPIC_API_KEY")

    def get_gemini_key(self) -> str:
        return self.get("GEMINI_API_KEY")

    # endregion


__all__ = ["SecretKeeper", "SecretManagerPlugin"]
