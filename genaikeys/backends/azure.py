import logging

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from ..plugins.base import SecretManagerPlugin
from ..settings.azure import AzureKeyVaultSettings

logger = logging.getLogger(__name__)


class AzureKeyVaultPlugin(SecretManagerPlugin):
    def __init__(self, vault_url: str | None = None):
        overrides = {}
        if vault_url is not None:
            overrides["azure_key_vault_url"] = vault_url
        cfg = AzureKeyVaultSettings(**overrides)

        credential = DefaultAzureCredential(
            managed_identity_client_id=cfg.managed_identity_client_id,
            exclude_interactive_browser_credential=not cfg.genaikeys_debug,
        )
        self.vault_url = cfg.azure_key_vault_url
        self.client = SecretClient(vault_url=self.vault_url, credential=credential)
        self._list_secrets_cache: dict[int, list[str]] = {}
        logger.debug(
            "Azure Key Vault client initialized (vault_url=%s, managed_identity=%s)",
            self.vault_url,
            bool(cfg.managed_identity_client_id),
        )

    @staticmethod
    def _standard_kv_secret_name(secret_name: str) -> str:
        return secret_name.replace("_", "-")

    def get_secret(self, secret_name: str) -> str:
        normalized = self._standard_kv_secret_name(secret_name)
        if normalized != secret_name:
            logger.debug("normalized secret name %r -> %r", secret_name, normalized)
        try:
            secret = self.client.get_secret(normalized)
        except Exception as exc:
            logger.error("Azure Key Vault get_secret failed for %r: %s", normalized, exc)
            raise
        value = secret.value
        if value is None:
            logger.warning("Azure Key Vault returned empty value for %r", normalized)
            raise KeyError(f"Secret '{normalized}' has no value")
        return value

    def list_secrets(self, max_results: int = 100) -> list[str]:
        if max_results in self._list_secrets_cache:
            return self._list_secrets_cache[max_results]
        result = [
            secret.name
            for secret in self.client.list_properties_of_secrets(max_page_size=max_results)
            if secret.name is not None
        ]
        self._list_secrets_cache[max_results] = result
        return result

    def exists(self, secret_name: str, **kwargs) -> bool:
        return self._standard_kv_secret_name(secret_name) in self.list_secrets(**kwargs)
