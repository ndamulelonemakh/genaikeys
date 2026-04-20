import abc
import asyncio


class SecretManagerPlugin(abc.ABC):
    @abc.abstractmethod
    def get_secret(self, secret_name: str) -> str:
        pass

    async def aget_secret(self, secret_name: str) -> str:
        return await asyncio.to_thread(self.get_secret, secret_name)

    def get_secrets(self, secret_names: list[str]) -> dict[str, str]:
        return {name: self.get_secret(name) for name in secret_names}

    def exists(self, secret_name: str, **kwargs) -> bool:
        raise NotImplementedError

    def list_secrets(self, max_results: int = 100) -> list[str]:
        raise NotImplementedError
