import functools
import os

from google.cloud import secretmanager_v1

from .types import SecretManagerPlugin


class GCPSecretManagerPlugin(SecretManagerPlugin):
    def __init__(self, project_id: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")):
        if not project_id:
            raise ValueError(
                "Google Cloud Project ID must be provided or set in GOOGLE_CLOUD_PROJECT environment variable")
        self.client = secretmanager_v1.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_name: str) -> str:
        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error: {e}")
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
        except Exception as e:
            if "NotFound" in str(e):
                return False
            else:
                raise
