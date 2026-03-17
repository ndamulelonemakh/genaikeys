"""
Azure Key Vault plugin for SecretKeeper.

Uses ``DefaultAzureCredential`` which walks the following chain and stops at the
first successful credential (keyless options are marked with ✓):

  1. EnvironmentCredential      – AZURE_TENANT_ID + AZURE_CLIENT_ID +
                                   AZURE_CLIENT_SECRET / AZURE_CLIENT_CERTIFICATE_PATH /
                                   AZURE_FEDERATED_TOKEN_FILE
  2. WorkloadIdentityCredential – ✓ Kubernetes projected OIDC token
                                   (AZURE_FEDERATED_TOKEN_FILE + AZURE_TENANT_ID +
                                    AZURE_CLIENT_ID — injected by the AKS webhook)
  3. ManagedIdentityCredential  – ✓ System-assigned or user-assigned Managed Identity
                                   on any Azure-hosted compute (VM, App Service, AKS
                                   node, Container Apps, Functions).  No credentials
                                   stored — token fetched from IMDS automatically.
  4. AzureCliCredential         – ✓ Developer workstation: ``az login`` session
  5. AzurePowerShellCredential  – ✓ Developer workstation: ``Connect-AzAccount``
  6. AzureDeveloperCliCredential– ✓ Developer workstation: ``azd auth login``
  7. InteractiveBrowserCredential – disabled by default; set SECRETKEEPER_DEBUG=1

Configuration (via environment variables or constructor kwargs):
    AZURE_KEY_VAULT_URL         – Full vault URL (required)
    MANAGED_IDENTITY_CLIENT_ID  – Client ID for a User-Assigned Managed Identity
    SECRETKEEPER_DEBUG          – Set to "1" to enable interactive browser login

Example:
    >>> from genaikeys import SecretKeeper
    >>> # Keyless on Azure-hosted compute (Managed Identity):
    >>> skp = SecretKeeper.azure(vault_url="https://my-vault.vault.azure.net/")
    >>> secret = skp.get("my-secret")
"""

import functools

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from ._settings import AzureKeyVaultSettings
from .types import SecretManagerPlugin


class AzureKeyVaultPlugin(SecretManagerPlugin):
    def __init__(self, vault_url: str | None = None):
        overrides = {}
        if vault_url is not None:
            overrides["azure_key_vault_url"] = vault_url
        cfg = AzureKeyVaultSettings(**overrides)

        credential = DefaultAzureCredential(
            managed_identity_client_id=cfg.managed_identity_client_id,
            exclude_interactive_browser_credential=not cfg.secretkeeper_debug,
        )
        self.vault_url = cfg.azure_key_vault_url
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
        return self._standard_kv_secret_name(secret_name) in self.list_secrets(**kwargs)
