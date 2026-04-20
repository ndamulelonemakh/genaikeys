import threading

from .cache import InMemorySecretManager
from .plugins import SecretManagerPlugin, load_backend


class SingletonMeta(type):
    _instances: dict[type, object] = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SecretKeeper(metaclass=SingletonMeta):
    def __init__(self, plugin: SecretManagerPlugin, cache_duration: int = 3600):
        self._manager = InMemorySecretManager(plugin, cache_duration)

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
