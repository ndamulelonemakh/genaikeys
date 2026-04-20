from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from genaikeys import GenAIKeys


class TestGenAIKeysFactories:
    def test_azure_factory_raises_without_url(self, mock_cloud_backends):
        with pytest.raises(ValidationError) as exc_info, patch.dict("os.environ", {}, clear=True):
            GenAIKeys.azure(vault_url=None)
        assert "azure_key_vault_url" in str(exc_info.value)

    def test_aws_factory_raises_without_region(self, mock_cloud_backends):
        with pytest.raises(ValidationError) as exc_info, patch.dict("os.environ", {}, clear=True):
            GenAIKeys.aws(region_name=None)
        assert "aws_default_region" in str(exc_info.value)

    def test_gcp_factory_raises_without_project(self, mock_cloud_backends):
        with pytest.raises(ValidationError) as exc_info, patch.dict("os.environ", {}, clear=True):
            GenAIKeys.gcp(project_id=None)
        assert "google_cloud_project" in str(exc_info.value)

    def test_azure_factory_with_explicit_url(self, mock_cloud_backends):
        import genaikeys.backends.azure as azure_backend

        mock_plugin = MagicMock()
        with patch.object(azure_backend, "AzureKeyVaultPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {}, clear=True):
                GenAIKeys.azure(vault_url="https://my-vault.vault.azure.net/")
            mock_constructor.assert_called_once_with(vault_url="https://my-vault.vault.azure.net/")

    def test_azure_factory_passes_none_when_url_omitted(self, mock_cloud_backends):
        import genaikeys.backends.azure as azure_backend

        mock_plugin = MagicMock()
        with patch.object(azure_backend, "AzureKeyVaultPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://my-vault.vault.azure.net/"}):
                GenAIKeys.azure()
            mock_constructor.assert_called_once_with(vault_url=None)

    def test_aws_factory_with_explicit_region(self, mock_cloud_backends):
        import genaikeys.backends.aws as aws_backend

        mock_plugin = MagicMock()
        with patch.object(aws_backend, "AWSSecretsManagerPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {}, clear=True):
                GenAIKeys.aws(region_name="eu-west-1")
            mock_constructor.assert_called_once_with(region_name="eu-west-1", profile_name=None)

    def test_aws_factory_passes_none_when_region_omitted(self, mock_cloud_backends):
        import genaikeys.backends.aws as aws_backend

        mock_plugin = MagicMock()
        with patch.object(aws_backend, "AWSSecretsManagerPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
                GenAIKeys.aws()
            mock_constructor.assert_called_once_with(region_name=None, profile_name=None)

    def test_aws_factory_with_profile_name(self, mock_cloud_backends):
        import genaikeys.backends.aws as aws_backend

        mock_plugin = MagicMock()
        with patch.object(aws_backend, "AWSSecretsManagerPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
                GenAIKeys.aws(profile_name="my-sso-profile")
            mock_constructor.assert_called_once_with(region_name=None, profile_name="my-sso-profile")

    def test_gcp_factory_with_explicit_project(self, mock_cloud_backends):
        import genaikeys.backends.gcp as gcp_backend

        mock_plugin = MagicMock()
        with patch.object(gcp_backend, "GCPSecretManagerPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {}, clear=True):
                GenAIKeys.gcp(project_id="my-project")
            mock_constructor.assert_called_once_with(project_id="my-project")

    def test_gcp_factory_passes_none_when_project_omitted(self, mock_cloud_backends):
        import genaikeys.backends.gcp as gcp_backend

        mock_plugin = MagicMock()
        with patch.object(gcp_backend, "GCPSecretManagerPlugin", return_value=mock_plugin) as mock_constructor:
            with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "env-project"}):
                GenAIKeys.gcp()
            mock_constructor.assert_called_once_with(project_id=None)
