import functools

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from ..plugins.base import SecretManagerPlugin
from ..settings.azure import AzureKeyVaultSettings


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
        self.client = SecretClient(vault_url=self.vault_url, credential=credential)

    @staticmethod
    def _standard_kv_secret_name(secret_name: str) -> str:
        return secret_name.replace("_", "-")

    def get_secret(self, secret_name: str) -> str:
        secret_name = self._standard_kv_secret_name(secret_name)
        secret = self.client.get_secret(secret_name)
        value = secret.value
        if value is None:
            raise KeyError(f"Secret '{secret_name}' has no value")
        return value

    @functools.lru_cache(maxsize=1, typed=True)
    def list_secrets(self, max_results: int = 100) -> list[str]:
        return [
            secret.name
            for secret in self.client.list_properties_of_secrets(max_page_size=max_results)
            if secret.name is not None
        ]

    def exists(self, secret_name: str, **kwargs) -> bool:
        return self._standard_kv_secret_name(secret_name) in self.list_secrets(**kwargs)
