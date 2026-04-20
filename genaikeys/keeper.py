import asyncio
import logging
import os
import re

from .cache import InMemorySecretManager
from .plugins import SecretManagerPlugin, load_backend

logger = logging.getLogger(__name__)

_SECRET_ATTR_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _is_secret_attr(name: str) -> bool:
    return bool(_SECRET_ATTR_RE.match(name))


class GenAIKeys:
    def __init__(
        self,
        plugin: SecretManagerPlugin,
        cache_duration: int = 3600,
        fallback_env: bool = False,
    ):
        self._manager = InMemorySecretManager(plugin, cache_duration)
        self._fallback_env = fallback_env
        logger.info(
            "GenAIKeys initialized (backend=%s, cache_duration=%ds, fallback_env=%s)",
            type(plugin).__name__,
            cache_duration,
            fallback_env,
        )

    @classmethod
    def from_defaults(cls, cache_duration: int = 3600, vault_url: str | None = None, fallback_env: bool = False):
        from .backends.azure import AzureKeyVaultPlugin

        return cls(AzureKeyVaultPlugin(vault_url=vault_url), cache_duration, fallback_env=fallback_env)

    @classmethod
    def azure(cls, cache_duration: int = 3600, vault_url: str | None = None, fallback_env: bool = False):
        return cls.from_defaults(cache_duration, vault_url, fallback_env=fallback_env)

    @classmethod
    def aws(
        cls,
        cache_duration: int = 3600,
        region_name: str | None = None,
        profile_name: str | None = None,
        fallback_env: bool = False,
    ):
        from .backends.aws import AWSSecretsManagerPlugin

        return cls(
            AWSSecretsManagerPlugin(region_name=region_name, profile_name=profile_name),
            cache_duration,
            fallback_env=fallback_env,
        )

    @classmethod
    def gcp(cls, cache_duration: int = 3600, project_id: str | None = None, fallback_env: bool = False):
        from .backends.gcp import GCPSecretManagerPlugin

        return cls(GCPSecretManagerPlugin(project_id=project_id), cache_duration, fallback_env=fallback_env)

    @classmethod
    def backend(cls, name: str, cache_duration: int = 3600, fallback_env: bool = False, **kwargs):
        backend_class = load_backend(name)
        return cls(backend_class(**kwargs), cache_duration, fallback_env=fallback_env)

    def _env_fallback(self, secret_name: str, exc: BaseException) -> str:
        value = os.environ.get(secret_name)
        if value is None:
            raise exc
        logger.warning(
            "backend lookup for %r failed (%s); using environment fallback",
            secret_name,
            type(exc).__name__,
        )
        return value

    def _resolve(self, secret_name: str) -> str:
        try:
            return self._manager.get_secret(secret_name)
        except Exception as exc:
            if not self._fallback_env:
                raise
            return self._env_fallback(secret_name, exc)

    async def _aresolve(self, secret_name: str) -> str:
        try:
            return await self._manager.aget_secret(secret_name)
        except Exception as exc:
            if not self._fallback_env:
                raise
            return self._env_fallback(secret_name, exc)

    def get_secret(self, secret_name: str) -> str:
        return self._resolve(secret_name)

    def get(self, secret_name: str) -> str:
        return self._resolve(secret_name)

    def get_many(self, secret_names: list[str]) -> dict[str, str]:
        return {name: self._resolve(name) for name in secret_names}

    def put(self, secret_name: str, value: str) -> None:
        self._manager._plugin.set_secret(secret_name, value)
        self._manager.invalidate_cache(secret_name=secret_name)

    def exists(self, secret_name: str) -> bool:
        return self._manager._plugin.exists(secret_name)

    def clear(self, secret_name: str | None = None):
        self._manager.invalidate_cache(secret_name=secret_name)

    def get_openai_key(self) -> str:
        return self.get("OPENAI_API_KEY")

    def get_anthropic_key(self) -> str:
        return self.get("ANTHROPIC_API_KEY")

    def get_gemini_key(self) -> str:
        return self.get("GEMINI_API_KEY")

    async def aget(self, secret_name: str) -> str:
        return await self._aresolve(secret_name)

    async def aget_many(self, secret_names: list[str]) -> dict[str, str]:
        values = await asyncio.gather(*(self._aresolve(name) for name in secret_names))
        return dict(zip(secret_names, values, strict=True))

    def __enter__(self) -> "GenAIKeys":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.clear()

    async def __aenter__(self) -> "GenAIKeys":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.clear()

    def __getattr__(self, name: str) -> str:
        if name.startswith("_") or not _is_secret_attr(name):
            raise AttributeError(name)
        try:
            return self._resolve(name)
        except Exception as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, name: str) -> str:
        return self._resolve(name)

    def __contains__(self, name: str) -> bool:
        try:
            self._resolve(name)
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
