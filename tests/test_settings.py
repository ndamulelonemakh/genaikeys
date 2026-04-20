from unittest.mock import patch

import pytest
from pydantic import ValidationError

from genaikeys.settings import AWSSettings, AzureKeyVaultSettings, GCPSettings


class TestAzureKeyVaultSettings:
    def test_reads_from_env(self):
        with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://vault.azure.net/"}):
            cfg = AzureKeyVaultSettings()
        assert cfg.azure_key_vault_url == "https://vault.azure.net/"
        assert cfg.managed_identity_client_id is None
        assert cfg.genaikeys_debug is False

    def test_constructor_override_takes_precedence(self):
        with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://env-vault.azure.net/"}):
            cfg = AzureKeyVaultSettings(azure_key_vault_url="https://override.azure.net/")
        assert cfg.azure_key_vault_url == "https://override.azure.net/"

    def test_optional_fields(self):
        with patch.dict(
            "os.environ",
            {
                "AZURE_KEY_VAULT_URL": "https://vault.azure.net/",
                "MANAGED_IDENTITY_CLIENT_ID": "my-client-id",
                "GENAIKEYS_DEBUG": "1",
            },
        ):
            cfg = AzureKeyVaultSettings()
        assert cfg.managed_identity_client_id == "my-client-id"
        assert cfg.genaikeys_debug is True

    def test_raises_when_url_missing(self):
        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValidationError) as exc_info:
            AzureKeyVaultSettings()
        assert "azure_key_vault_url" in str(exc_info.value)

    def test_extra_env_vars_ignored(self):
        with patch.dict(
            "os.environ",
            {
                "AZURE_KEY_VAULT_URL": "https://vault.azure.net/",
                "SOME_RANDOM_VAR": "noise",
            },
        ):
            cfg = AzureKeyVaultSettings()
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
        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValidationError) as exc_info:
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
        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValidationError) as exc_info:
            GCPSettings()
        assert "google_cloud_project" in str(exc_info.value)
