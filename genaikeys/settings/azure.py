from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureKeyVaultSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    azure_key_vault_url: str
    managed_identity_client_id: str | None = None
    secretkeeper_debug: bool = False
