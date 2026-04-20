import logging
import re

from .cache import InMemorySecretManager
from .plugins import SecretManagerPlugin, load_backend

logger = logging.getLogger(__name__)

_SECRET_ATTR_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _is_secret_attr(name: str) -> bool:
    return bool(_SECRET_ATTR_RE.match(name))


class GenAIKeys:
    def __init__(self, plugin: SecretManagerPlugin, cache_duration: int = 3600):
        self._manager = InMemorySecretManager(plugin, cache_duration)
        logger.info(
            "GenAIKeys initialized (backend=%s, cache_duration=%ds)",
            type(plugin).__name__,
            cache_duration,
        )

    @classmethod
    def from_defaults(cls, cache_duration: int = 3600, vault_url: str | None = None):
        from .backends.azure import AzureKeyVaultPlugin

        return cls(AzureKeyVaultPlugin(vault_url=vault_url), cache_duration)

    @classmethod
    def azure(cls, cache_duration: int = 3600, vault_url: str | None = None):
        return cls.from_defaults(cache_duration, vault_url)

    @classmethod
    def aws(cls, cache_duration: int = 3600, region_name: str | None = None, profile_name: str | None = None):
        from .backends.aws import AWSSecretsManagerPlugin

        return cls(AWSSecretsManagerPlugin(region_name=region_name, profile_name=profile_name), cache_duration)

    @classmethod
    def gcp(cls, cache_duration: int = 3600, project_id: str | None = None):
        from .backends.gcp import GCPSecretManagerPlugin

        return cls(GCPSecretManagerPlugin(project_id=project_id), cache_duration)

    @classmethod
    def backend(cls, name: str, cache_duration: int = 3600, **kwargs):
        backend_class = load_backend(name)
        return cls(backend_class(**kwargs), cache_duration)

    def get_secret(self, secret_name: str) -> str:
        return self._manager.get_secret(secret_name)

    def get(self, secret_name: str) -> str:
        return self.get_secret(secret_name)

    def clear(self, secret_name: str | None = None):
        self._manager.invalidate_cache(secret_name=secret_name)

    def get_openai_key(self) -> str:
        return self.get("OPENAI_API_KEY")

    def get_anthropic_key(self) -> str:
        return self.get("ANTHROPIC_API_KEY")

    def get_gemini_key(self) -> str:
        return self.get("GEMINI_API_KEY")

    def __enter__(self) -> "GenAIKeys":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.clear()

    def __getattr__(self, name: str) -> str:
        if name.startswith("_") or not _is_secret_attr(name):
            raise AttributeError(name)
        try:
            return self._manager.get_secret(name)
        except Exception as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, name: str) -> str:
        return self._manager.get_secret(name)

    def __contains__(self, name: str) -> bool:
        try:
            self._manager.get_secret(name)
        except Exception:
            return False
        return True

    def __repr__(self) -> str:
        return "<GenAIKeys>"

    def __reduce__(self):
        raise TypeError("GenAIKeys is not picklable: refusing to serialize cached secrets")

    def __copy__(self):
        raise TypeError("GenAIKeys is not copyable: refusing to duplicate cached secrets")

    def __deepcopy__(self, memo):
        raise TypeError("GenAIKeys is not copyable: refusing to duplicate cached secrets")
