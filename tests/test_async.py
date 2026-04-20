import pytest

from genaikeys import GenAIKeys
from tests.helpers import FakePlugin


@pytest.mark.asyncio
class TestAsyncAPI:
    async def test_aget_returns_secret(self):
        plugin = FakePlugin({"OPENAI_API_KEY": "sk-test-123"})
        sk = GenAIKeys(plugin)
        value = await sk.aget("OPENAI_API_KEY")
        assert value == "sk-test-123"

    async def test_aget_uses_cache(self):
        plugin = FakePlugin({"K": "v"})
        sk = GenAIKeys(plugin)
        await sk.aget("K")
        await sk.aget("K")
        assert plugin.call_count == 1

    async def test_aget_many_returns_dict(self):
        plugin = FakePlugin({"A": "1", "B": "2", "C": "3"})
        sk = GenAIKeys(plugin)
        result = await sk.aget_many(["A", "B", "C"])
        assert result == {"A": "1", "B": "2", "C": "3"}
        assert plugin.call_count == 3

    async def test_aget_many_uses_cache(self):
        plugin = FakePlugin({"A": "1", "B": "2"})
        sk = GenAIKeys(plugin)
        sk.get("A")
        result = await sk.aget_many(["A", "B"])
        assert result == {"A": "1", "B": "2"}
        assert plugin.call_count == 2

    async def test_aget_raises_on_missing(self):
        plugin = FakePlugin({})
        sk = GenAIKeys(plugin)
        with pytest.raises(KeyError):
            await sk.aget("NOPE")

    async def test_async_context_manager(self):
        plugin = FakePlugin({"K": "v"})
        async with GenAIKeys(plugin) as sk:
            await sk.aget("K")
            assert plugin.call_count == 1
            await sk.aget("K")
            assert plugin.call_count == 1
        await sk.aget("K")
        assert plugin.call_count == 2

    async def test_sync_and_async_share_cache(self):
        plugin = FakePlugin({"K": "v"})
        sk = GenAIKeys(plugin)
        sk.get("K")
        value = await sk.aget("K")
        assert value == "v"
        assert plugin.call_count == 1
