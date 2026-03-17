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

    @functools.lru_cache(maxsize=1, typed=True)
    def list_secrets(self, max_results: int = 100) -> list[str]:
        parent = f"projects/{self.project_id}"
        response = self.client.list_secrets(request={"parent": parent, "pageSize": max_results})
        return [secret.name.split('/')[-1] for secret in response]

    def exists(self, secret_name: str, **kwargs) -> bool:
        name = f"projects/{self.project_id}/secrets/{secret_name}"
        try:
            self.client.get_secret(request={"name": name})
            return True
        except NotFound:
            return False
