"""
Azure Key Vault plugin for SecretKeeper.

This module provides integration with Azure Key Vault for secret management.
It uses Azure's DefaultAzureCredential for authentication with RBAC.

Configuration:
    The following environment variables can be used:
    - AZURE_KEY_VAULT_URL: URL of your Azure Key Vault (required if not passed to constructor)
    - MANAGED_IDENTITY_CLIENT_ID: Client ID for managed identity authentication (optional)

Example:
    >>> from genaikeys import SecretKeeper
    >>> # Using environment variables
    >>> skp = SecretKeeper.azure(vault_url="https://my-vault.vault.azure.net/")
    >>> secret = skp.get("my-secret")
"""

import functools
import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from ._secret_manager import SecretManagerPlugin


class AzureKeyVaultPlugin(SecretManagerPlugin):
    def __init__(self, vault_url: str | None = None):
        self.vault_url = vault_url or os.environ.get("AZURE_KEY_VAULT_URL")
        if not self.vault_url:
            raise ValueError("Azure Key Vault URL must be provided or set in AZURE_KEY_VAULT_URL environment variable")
        credential = DefaultAzureCredential(
            managed_identity_client_id=os.environ.get("MANGED_IDENTITY_CLIENT_ID"),
            exclude_interactive_browser_credential=not os.getenv("SECRETKEEPER_DEBUG", "0") == "1"
        )
        # noinspection PyTypeChecker
        self.client = SecretClient(vault_url=self.vault_url, credential=credential)

    @staticmethod
    def _standard_kv_secret_name(secret_name: str) -> str:
        return secret_name.replace("_", "-")

    def get_secret(self, secret_name: str) -> str:
        secret_name = self._standard_kv_secret_name(secret_name)
        secret = self.client.get_secret(secret_name)
        return secret.value

    @functools.lru_cache(maxsize=1, typed=True)
    def list_secrets(self, max_results: int = 100) -> list[str]:
        return [secret.name
                for secret in self.client.list_properties_of_secrets(max_page_size=max_results)]

    def exists(self, secret_name: str, **kwargs) -> bool:
        return secret_name in self.list_secrets(**kwargs)
