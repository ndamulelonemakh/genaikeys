"""
Pydantic BaseSettings models for each secret-backend.

Each class maps environment variables (uppercased field name by default) to
typed, validated Python attributes.  Callers can override individual fields via
constructor kwargs, which takes precedence over the environment — so passing
``vault_url`` explicitly still works while falling back to the env var when it
is not supplied.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureKeyVaultSettings(BaseSettings):
    """Configuration for the Azure Key Vault backend.

    Environment variables (all case-insensitive):
        AZURE_KEY_VAULT_URL         – Full vault URL (required)
        MANAGED_IDENTITY_CLIENT_ID  – User-Assigned Managed Identity client ID
        SECRETKEEPER_DEBUG          – Set to "1" to allow interactive browser login
    """

    model_config = SettingsConfigDict(extra="ignore")

    azure_key_vault_url: str
    managed_identity_client_id: Optional[str] = None
    secretkeeper_debug: bool = False


class AWSSettings(BaseSettings):
    """Configuration for the AWS Secrets Manager backend.

    Environment variables:
        AWS_DEFAULT_REGION  – AWS region where secrets are stored (required)
    """

    model_config = SettingsConfigDict(extra="ignore")

    aws_default_region: str


class GCPSettings(BaseSettings):
    """Configuration for the Google Secret Manager backend.

    Environment variables:
        GOOGLE_CLOUD_PROJECT  – GCP project ID (required)
    """

    model_config = SettingsConfigDict(extra="ignore")

    google_cloud_project: str
