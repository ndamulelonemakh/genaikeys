import os
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
        from ._azure_keyvault import AzureKeyVaultPlugin

        vault_url = vault_url or os.environ.get("AZURE_KEY_VAULT_URL")
        if not vault_url:
            raise ValueError("Azure Key Vault URL must be provided or set in AZURE_KEY_VAULT_URL environment variable")

        secret_store = AzureKeyVaultPlugin(vault_url=vault_url)
        return cls(secret_store, cache_duration)

    @classmethod
    def azure(cls, cache_duration: int = 3600, vault_url: Optional[str] = None):
        return cls.from_defaults(cache_duration, vault_url)

    @classmethod
    def aws(cls, cache_duration: int = 3600, region_name: Optional[str] = None):
        from ._aws_secret_manager import AWSSecretsManagerPlugin

        region_name = region_name or os.getenv("AWS_DEFAULT_REGION")
        if not region_name:
            raise ValueError("AWS region must be provided or set in AWS_DEFAULT_REGION environment variable")

        secret_store = AWSSecretsManagerPlugin(region_name=region_name)
        return cls(secret_store, cache_duration)

    @classmethod
    def gcp(cls, cache_duration: int = 3600, project_id: Optional[str] = None):
        from ._gcp_secret_manager import GCPSecretManagerPlugin

        secret_store = GCPSecretManagerPlugin(project_id=project_id) if project_id else GCPSecretManagerPlugin()
        return cls(secret_store, cache_duration)

    def get_secret(self, secret_name: str) -> str:
        secret_value = self._manager.get_secret(secret_name)
        os.environ[secret_name] = secret_value
        return secret_value

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
