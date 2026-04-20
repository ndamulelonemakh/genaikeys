"""Logging configuration helpers for genaikeys.

The library follows the standard Python pattern of attaching a
:class:`logging.NullHandler` to the top-level package logger. By default the
library emits no output; clients retain full control over format, level and
destination via the standard :mod:`logging` configuration.

Use :func:`enable_logging` for a one-line opt-in during local debugging.
Production code should configure the ``"genaikeys"`` logger directly.
"""

from __future__ import annotations

import logging

_PACKAGE_LOGGER = "genaikeys"
_DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def enable_logging(
    level: int | str = logging.INFO,
    *,
    handler: logging.Handler | None = None,
    fmt: str = _DEFAULT_FORMAT,
    propagate: bool = False,
) -> logging.Logger:
    logger = logging.getLogger(_PACKAGE_LOGGER)
    logger.setLevel(level)
    logger.propagate = propagate

    if handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))

    for existing in logger.handlers:
        if getattr(existing, "_genaikeys_managed", False):
            logger.removeHandler(existing)

    handler._genaikeys_managed = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    return logger


def disable_logging() -> None:
    logger = logging.getLogger(_PACKAGE_LOGGER)
    for existing in list(logger.handlers):
        if getattr(existing, "_genaikeys_managed", False):
            logger.removeHandler(existing)
    logger.setLevel(logging.WARNING)
