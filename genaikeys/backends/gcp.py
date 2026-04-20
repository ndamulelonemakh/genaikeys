import logging

from google.api_core.exceptions import NotFound
from google.cloud import secretmanager_v1

from ..plugins.base import SecretManagerPlugin
from ..settings.gcp import GCPSettings

logger = logging.getLogger(__name__)


class GCPSecretManagerPlugin(SecretManagerPlugin):
    def __init__(self, project_id: str | None = None):
        overrides = {}
        if project_id is not None:
            overrides["google_cloud_project"] = project_id
        cfg = GCPSettings(**overrides)
        self.client = secretmanager_v1.SecretManagerServiceClient()
        self.project_id = cfg.google_cloud_project
        self._list_secrets_cache: dict[int, list[str]] = {}
        logger.debug("GCP Secret Manager client initialized (project=%s)", self.project_id)

    def get_secret(self, secret_name: str) -> str:
        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        logger.debug("GCP access_secret_version name=%s", name)
        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as exc:
            logger.error("GCP access_secret_version failed for %r: %s", secret_name, type(exc).__name__)
            raise

    def list_secrets(self, max_results: int = 100) -> list[str]:
        if max_results in self._list_secrets_cache:
            return self._list_secrets_cache[max_results]
        parent = f"projects/{self.project_id}"
        response = self.client.list_secrets(request={"parent": parent, "pageSize": max_results})
        result = [secret.name.split("/")[-1] for secret in response]
        self._list_secrets_cache[max_results] = result
        return result

    def exists(self, secret_name: str, **kwargs) -> bool:
        name = f"projects/{self.project_id}/secrets/{secret_name}"
        try:
            self.client.get_secret(request={"name": name})
            return True
        except NotFound:
            return False
