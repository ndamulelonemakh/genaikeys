from genaikeys import SecretManagerPlugin


class FakePlugin(SecretManagerPlugin):
    def __init__(self, secrets: dict | None = None):
        self._secrets = secrets or {}
        self.call_count = 0

    def get_secret(self, secret_name: str) -> str:
        self.call_count += 1
        if secret_name not in self._secrets:
            raise KeyError(f"Secret '{secret_name}' not found")
        return self._secrets[secret_name]

    def exists(self, secret_name: str, **kwargs) -> bool:
        return secret_name in self._secrets

    def list_secrets(self, max_results: int = 100) -> list[str]:
        return list(self._secrets.keys())[:max_results]
