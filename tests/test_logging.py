import logging

import pytest

from genaikeys import GenAIKeys
from tests.helpers import FakePlugin


class TestLogging:
    def test_package_logger_has_null_handler_by_default(self):
        import genaikeys

        pkg_logger = logging.getLogger("genaikeys")
        assert any(isinstance(handler, logging.NullHandler) for handler in pkg_logger.handlers)
        assert genaikeys

    def test_no_secret_value_in_logs(self, caplog):
        plugin = FakePlugin({"OPENAI_API_KEY": "super-secret-value-xyz"})
        sk = GenAIKeys(plugin)
        with caplog.at_level(logging.DEBUG, logger="genaikeys"):
            sk.get("OPENAI_API_KEY")
        joined = "\n".join(record.getMessage() for record in caplog.records)
        assert "super-secret-value-xyz" not in joined
        assert "OPENAI_API_KEY" in joined

    def test_cache_hit_emits_debug(self, caplog):
        plugin = FakePlugin({"FOO": "bar"})
        sk = GenAIKeys(plugin)
        sk.get("FOO")
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="genaikeys.cache"):
            sk.get("FOO")
        assert any("cache hit" in record.getMessage() for record in caplog.records)

    def test_backend_failure_logged_as_warning(self, caplog):
        plugin = FakePlugin({})
        sk = GenAIKeys(plugin)
        with caplog.at_level(logging.WARNING, logger="genaikeys.cache"), pytest.raises(KeyError):
            sk.get("NOPE")
        assert any(record.levelno == logging.WARNING for record in caplog.records)

    def test_enable_logging_attaches_handler(self):
        from genaikeys import disable_logging, enable_logging

        try:
            logger = enable_logging(level=logging.DEBUG)
            assert logger.level == logging.DEBUG
            assert any(getattr(handler, "_genaikeys_managed", False) for handler in logger.handlers)
            enable_logging(level=logging.INFO)
            managed = [handler for handler in logger.handlers if getattr(handler, "_genaikeys_managed", False)]
            assert len(managed) == 1
        finally:
            disable_logging()

    def test_disable_logging_removes_managed_handlers(self):
        from genaikeys import disable_logging, enable_logging

        enable_logging(level=logging.DEBUG)
        disable_logging()
        logger = logging.getLogger("genaikeys")
        assert not any(getattr(handler, "_genaikeys_managed", False) for handler in logger.handlers)
