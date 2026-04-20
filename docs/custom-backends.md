# Custom Backends

GenAIKeys provides a plugin interface so you can integrate any secret store.

## Implementing a Plugin

Subclass `SecretManagerPlugin` and implement the `get_secret` method:

```python
from genaikeys import GenAIKeys
from genaikeys.plugins import SecretManagerPlugin


class HashiCorpVaultPlugin(SecretManagerPlugin):
    """Example: retrieve secrets from HashiCorp Vault."""

    def __init__(self, vault_addr: str, token: str):
        import hvac
        self.client = hvac.Client(url=vault_addr, token=token)

    def get_secret(self, secret_name: str) -> str:
        response = self.client.secrets.kv.v2.read_secret_version(path=secret_name)
        return response["data"]["data"]["value"]

    def exists(self, secret_name: str, **kwargs) -> bool:
        try:
            self.get_secret(secret_name)
            return True
        except Exception:
            return False

    def list_secrets(self, max_results: int = 100) -> list[str]:
        response = self.client.secrets.kv.v2.list_secrets(path="")
        return response["data"]["keys"][:max_results]


# Use it
sk = GenAIKeys(HashiCorpVaultPlugin(
    vault_addr="https://vault.example.com",
    token="hvs.xxx",
))
key = sk.get("OPENAI_API_KEY")
```

## Plugin Interface

```python
class SecretManagerPlugin(abc.ABC):
    @abc.abstractmethod
    def get_secret(self, secret_name: str) -> str:
        """Retrieve a secret value by name. Must be implemented."""
        ...

    def exists(self, secret_name: str, **kwargs) -> bool:
        """Check if a secret exists. Optional — raises NotImplementedError by default."""
        ...

    def list_secrets(self, max_results: int = 100) -> list[str]:
        """List available secret names. Optional — raises NotImplementedError by default."""
        ...
```

Only `get_secret` is required. The `exists` and `list_secrets` methods are optional
and raise `NotImplementedError` by default.

If your backend is expensive to probe, you can omit `exists` and `list_secrets`
entirely. `GenAIKeys.get()` only requires `get_secret()`.

## Caching

Your custom plugin automatically gets in-memory caching when passed to `GenAIKeys`:

```python
# Cache secrets for 10 minutes
sk = GenAIKeys(MyPlugin(), cache_duration=600)
```

## Backend Discovery

The built-in backends live under `genaikeys.backends`. Third-party packages can
register their own backend class in the `genaikeys.backends` entry-point group
and users can instantiate it with `GenAIKeys.backend("your-backend", **kwargs)`.

You can also inspect or resolve registered backends directly:

```python
from genaikeys.plugins import available_backends, load_backend

print(available_backends())
plugin_class = load_backend("your-backend")
```
