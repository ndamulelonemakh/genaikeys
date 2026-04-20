"""
Google Secret Manager plugin for SecretKeeper.

Uses Application Default Credentials (ADC) which resolves in this order:

  1. GOOGLE_APPLICATION_CREDENTIALS env var → JSON file (service account key OR
     Workload Identity Federation config — the WIF config contains no secrets,
     only metadata instructing the library how to exchange an external OIDC/SAML
     token for a GCP access token).
  2. ~/.config/gcloud/application_default_credentials.json  – created by
     ``gcloud auth application-default login`` (developer workstations).
  3. Metadata server (169.254.169.254)   – ✓ automatic on GCE, GKE, Cloud Run,
     Cloud Functions, App Engine, Vertex AI.  The attached service account token
     is fetched transparently; no credentials stored in code or config.

Keyless options:
    GKE Workload Identity – bind a Kubernetes SA to a GCP SA via IAM; the pod's
        projected OIDC token is exchanged for a GCP token via the metadata server.
    Workload Identity Federation – run on AWS / Azure / GitHub Actions / any OIDC
        IdP; generate a credential config with ``gcloud iam workload-identity-pools
        create-cred-config`` and set GOOGLE_APPLICATION_CREDENTIALS to point at it.

Configuration:
    GOOGLE_CLOUD_PROJECT          – GCP project ID (required)
    GOOGLE_APPLICATION_CREDENTIALS – Path to credential JSON (optional; ADC reads
                                     this automatically)
"""

import functools
import logging

from google.api_core.exceptions import NotFound
from google.cloud import secretmanager_v1

from ._settings import GCPSettings
from .types import SecretManagerPlugin

logger = logging.getLogger(__name__)


class GCPSecretManagerPlugin(SecretManagerPlugin):
    def __init__(self, project_id: str | None = None):
        overrides = {}
        if project_id is not None:
            overrides["google_cloud_project"] = project_id
        cfg = GCPSettings(**overrides)
        self.client = secretmanager_v1.SecretManagerServiceClient()
        self.project_id = cfg.google_cloud_project

    def get_secret(self, secret_name: str) -> str:
        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error("Failed to retrieve secret '%s': %s", secret_name, e)
            raise

    @functools.lru_cache(maxsize=1, typed=True)  # noqa: B019
    def list_secrets(self, max_results: int = 100) -> list[str]:
        parent = f"projects/{self.project_id}"
        response = self.client.list_secrets(request={"parent": parent, "pageSize": max_results})
        return [secret.name.split("/")[-1] for secret in response]

    def exists(self, secret_name: str, **kwargs) -> bool:
        name = f"projects/{self.project_id}/secrets/{secret_name}"
        try:
            self.client.get_secret(request={"name": name})
            return True
        except NotFound:
            return False
