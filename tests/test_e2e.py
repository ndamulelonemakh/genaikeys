"""Live backend tests. Run with `pytest -m e2e` after setting the provider-specific env vars."""

import os

import pytest


def _require_env(*names: str, mark: str) -> None:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        pytest.skip(f"[{mark}] required env var(s) not set: {', '.join(missing)}")


@pytest.mark.e2e
@pytest.mark.aws
class TestAWSE2E:
    @pytest.fixture(autouse=True)
    def _check_prereqs(self):
        pytest.importorskip("boto3", reason="boto3 not installed (pip install genaikeys[aws])")
        _require_env("AWS_DEFAULT_REGION", "E2E_AWS_SECRET_NAME", mark="aws")

    @pytest.fixture
    def plugin(self):
        from genaikeys.backends.aws import AWSSecretsManagerPlugin

        return AWSSecretsManagerPlugin(
            region_name=os.environ["AWS_DEFAULT_REGION"],
            profile_name=os.environ.get("AWS_PROFILE"),
        )

    def test_get_secret(self, plugin):
        secret_name = os.environ["E2E_AWS_SECRET_NAME"]
        value = plugin.get_secret(secret_name)
        assert isinstance(value, str) and value, "expected a non-empty string"
        expected = os.environ.get("E2E_AWS_SECRET_EXPECTED_VALUE")
        if expected:
            assert value == expected, f"value mismatch: got {value!r}"

    def test_exists_returns_true_for_known_secret(self, plugin):
        secret_name = os.environ["E2E_AWS_SECRET_NAME"]
        assert plugin.exists(secret_name) is True

    def test_exists_returns_false_for_unknown_secret(self, plugin):
        assert plugin.exists("__genaikeys_e2e_nonexistent_secret__") is False

    def test_list_secrets_contains_known_secret(self, plugin):
        secret_name = os.environ["E2E_AWS_SECRET_NAME"]
        secrets = plugin.list_secrets()
        assert isinstance(secrets, list)
        assert secret_name in secrets, (
            f"{secret_name!r} not found in list_secrets() — check IAM permissions (secretsmanager:ListSecrets)"
        )


@pytest.mark.e2e
@pytest.mark.azure
class TestAzureE2E:
    @pytest.fixture(autouse=True)
    def _check_prereqs(self):
        pytest.importorskip(
            "azure.keyvault.secrets",
            reason="azure-keyvault-secrets not installed (pip install genaikeys[azure])",
        )
        _require_env("AZURE_KEY_VAULT_URL", "E2E_AZURE_SECRET_NAME", mark="azure")

    @pytest.fixture
    def plugin(self):
        from genaikeys.backends.azure import AzureKeyVaultPlugin

        return AzureKeyVaultPlugin(vault_url=os.environ["AZURE_KEY_VAULT_URL"])

    def test_get_secret(self, plugin):
        secret_name = os.environ["E2E_AZURE_SECRET_NAME"]
        value = plugin.get_secret(secret_name)
        assert isinstance(value, str) and value, "expected a non-empty string"
        expected = os.environ.get("E2E_AZURE_SECRET_EXPECTED_VALUE")
        if expected:
            assert value == expected, f"value mismatch: got {value!r}"

    def test_exists_returns_true_for_known_secret(self, plugin):
        secret_name = os.environ["E2E_AZURE_SECRET_NAME"]
        assert plugin.exists(secret_name) is True

    def test_exists_returns_false_for_unknown_secret(self, plugin):
        assert plugin.exists("genaikeys-e2e-nonexistent-secret") is False

    def test_list_secrets_contains_known_secret(self, plugin):
        secret_name = os.environ["E2E_AZURE_SECRET_NAME"]
        secrets = plugin.list_secrets()
        assert isinstance(secrets, list)
        assert secret_name in secrets, (
            f"{secret_name!r} not found in list_secrets() — check Key Vault RBAC (Key Vault Secrets User role)"
        )


@pytest.mark.e2e
@pytest.mark.gcp
class TestGCPE2E:
    @pytest.fixture(autouse=True)
    def _check_prereqs(self):
        pytest.importorskip(
            "google.cloud.secretmanager_v1",
            reason=("google-cloud-secret-manager not installed (pip install genaikeys[gcp])"),
        )
        _require_env("GOOGLE_CLOUD_PROJECT", "E2E_GCP_SECRET_NAME", mark="gcp")

    @pytest.fixture
    def plugin(self):
        from genaikeys.backends.gcp import GCPSecretManagerPlugin

        return GCPSecretManagerPlugin(project_id=os.environ["GOOGLE_CLOUD_PROJECT"])

    def test_get_secret(self, plugin):
        secret_name = os.environ["E2E_GCP_SECRET_NAME"]
        value = plugin.get_secret(secret_name)
        assert isinstance(value, str) and value, "expected a non-empty string"
        expected = os.environ.get("E2E_GCP_SECRET_EXPECTED_VALUE")
        if expected:
            assert value == expected, f"value mismatch: got {value!r}"

    def test_exists_returns_true_for_known_secret(self, plugin):
        secret_name = os.environ["E2E_GCP_SECRET_NAME"]
        assert plugin.exists(secret_name) is True

    def test_exists_returns_false_for_unknown_secret(self, plugin):
        assert plugin.exists("genaikeys-e2e-nonexistent-secret") is False

    def test_list_secrets_contains_known_secret(self, plugin):
        secret_name = os.environ["E2E_GCP_SECRET_NAME"]
        secrets = plugin.list_secrets()
        assert isinstance(secrets, list)
        assert secret_name in secrets, (
            f"{secret_name!r} not found in list_secrets() — check IAM binding (roles/secretmanager.viewer)"
        )
