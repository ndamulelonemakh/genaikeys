import abc


class SecretManagerPlugin(abc.ABC):
    @abc.abstractmethod
    def get_secret(self, secret_name: str) -> str:
        pass

    def exists(self, secret_name: str, **kwargs) -> bool:
        raise NotImplementedError

    def list_secrets(self, max_results: int = 100) -> list[str]:
        raise NotImplementedError
