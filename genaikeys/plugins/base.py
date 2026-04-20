import abc
import asyncio


class SecretManagerPlugin(abc.ABC):
    @abc.abstractmethod
    def get_secret(self, secret_name: str) -> str:
        pass

    async def aget_secret(self, secret_name: str) -> str:
        return await asyncio.to_thread(self.get_secret, secret_name)

    def exists(self, secret_name: str, **kwargs) -> bool:
        raise NotImplementedError

    def list_secrets(self, max_results: int = 100) -> list[str]:
        raise NotImplementedError
