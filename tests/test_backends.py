from unittest.mock import MagicMock, patch


class TestAzureKeyVaultPlugin:
    def test_exists_normalises_underscores_to_dashes(self, mock_cloud_backends):
        import genaikeys.backends.azure as azure_backend

        mock_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.name = "my-secret"
        mock_client.list_properties_of_secrets.return_value = [mock_secret]

        with patch.dict("os.environ", {"AZURE_KEY_VAULT_URL": "https://vault.azure.net/"}):
            plugin = azure_backend.AzureKeyVaultPlugin()
        plugin.client = mock_client

        assert plugin.exists("my_secret") is True
        assert plugin.exists("my-secret") is True
        assert plugin.exists("OTHER_SECRET") is False


class TestAWSSecretsManagerPlugin:
    def test_session_created_without_profile(self, mock_cloud_backends):
        import genaikeys.backends.aws as aws_backend

        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        with patch.object(aws_backend.boto3, "Session", return_value=mock_session) as mock_constructor:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
                aws_backend.AWSSecretsManagerPlugin(region_name="eu-west-1")
            mock_constructor.assert_called_once_with(profile_name=None, region_name="eu-west-1")
            mock_session.client.assert_called_once_with("secretsmanager")

    def test_session_created_with_profile(self, mock_cloud_backends):
        import genaikeys.backends.aws as aws_backend

        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        with patch.object(aws_backend.boto3, "Session", return_value=mock_session) as mock_constructor:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1"}):
                aws_backend.AWSSecretsManagerPlugin(region_name="eu-west-1", profile_name="my-sso")
            mock_constructor.assert_called_once_with(profile_name="my-sso", region_name="eu-west-1")

    def test_profile_from_env_var(self, mock_cloud_backends):
        import genaikeys.backends.aws as aws_backend

        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        with patch.object(aws_backend.boto3, "Session", return_value=mock_session) as mock_constructor:
            with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "eu-west-1", "AWS_PROFILE": "sso-dev"}):
                aws_backend.AWSSecretsManagerPlugin(region_name="eu-west-1")
            mock_constructor.assert_called_once_with(profile_name="sso-dev", region_name="eu-west-1")
