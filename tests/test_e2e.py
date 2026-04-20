"""
End-to-end tests against real cloud backends.

These tests make real network calls and require valid credentials.  They are
**skipped automatically** when the relevant environment variables are absent or
the optional cloud SDK extras are not installed.

Run all e2e tests::

    pytest -m e2e -v

Run a single backend::

    pytest -m "e2e and aws"   -v
    pytest -m "e2e and azure" -v
    pytest -m "e2e and gcp"   -v

Required environment variables
-------------------------------
AWS
  AWS_DEFAULT_REGION        Region where secrets live (e.g. ``eu-west-1``)
  E2E_AWS_SECRET_NAME       Name of an existing secret to read
  Credentials (any one):
    AWS_PROFILE             Named profile (``aws configure sso``)
    AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
    IAM instance profile / IRSA (auto-detected, no extra vars needed)

Azure
  AZURE_KEY_VAULT_URL       Full vault URL (e.g. ``https://my-vault.vault.azure.net/``)
  E2E_AZURE_SECRET_NAME     Name of an existing secret to read
  Credentials (any one):
    ``az login`` session
    AZURE_CLIENT_ID + AZURE_TENANT_ID + AZURE_CLIENT_SECRET / AZURE_CLIENT_CERTIFICATE_PATH
    Managed Identity (auto-detected on Azure-hosted compute)

GCP
  GOOGLE_CLOUD_PROJECT      GCP project ID
  E2E_GCP_SECRET_NAME       Name of an existing secret to read
  Credentials (any one):
    ``gcloud auth application-default login``
    GOOGLE_APPLICATION_CREDENTIALS (service-account key or WIF config)
    Attached service account (auto-detected on GCE/GKE/Cloud Run/etc.)

Optional assertion
  E2E_<PROVIDER>_SECRET_EXPECTED_VALUE
    When set the test asserts that the fetched secret value matches exactly.
    Useful for CI pipelines where the test secret value is known.
"""

import os

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_env(*names: str, mark: str) -> None:
    """Skip the test if any of *names* is unset."""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        pytest.skip(f"[{mark}] required env var(s) not set: {', '.join(missing)}")


# ---------------------------------------------------------------------------
# AWS Secrets Manager
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.aws
class TestAWSE2E:
    """Live tests against AWS Secrets Manager.

    The boto3 credential chain is used — any valid credential source (instance
    profile, IRSA, named profile, static keys) will work.
    """

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


# ---------------------------------------------------------------------------
# Azure Key Vault
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.azure
class TestAzureE2E:
    """Live tests against Azure Key Vault.

    DefaultAzureCredential is used — any credential source in the chain
    (Managed Identity, az login, AZURE_CLIENT_* env vars, etc.) will work.
    """

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


# ---------------------------------------------------------------------------
# GCP Secret Manager
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.gcp
class TestGCPE2E:
    """Live tests against Google Secret Manager.

    Application Default Credentials (ADC) are used — any credential source
    (gcloud ADC, GOOGLE_APPLICATION_CREDENTIALS, metadata server) will work.
    """

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
