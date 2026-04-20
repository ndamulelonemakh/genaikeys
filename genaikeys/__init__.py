import logging as _stdlib_logging
from importlib.metadata import PackageNotFoundError, version

from ._logging import disable_logging, enable_logging
from .keeper import GenAIKeys, SingletonMeta
from .plugins import SecretManagerPlugin

try:
    __version__ = version("genaikeys")
except PackageNotFoundError:
    __version__ = "unknown"

_stdlib_logging.getLogger(__name__).addHandler(_stdlib_logging.NullHandler())

__all__ = [
    "GenAIKeys",
    "SecretManagerPlugin",
    "SingletonMeta",
    "__version__",
    "enable_logging",
    "disable_logging",
]
