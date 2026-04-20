from importlib.metadata import entry_points

from .base import SecretManagerPlugin

BACKEND_ENTRYPOINT_GROUP = "genaikeys.backends"


def available_backends() -> list[str]:
    return sorted(entry_point.name for entry_point in entry_points(group=BACKEND_ENTRYPOINT_GROUP))


def load_backend(name: str) -> type[SecretManagerPlugin]:
    for entry_point in entry_points(group=BACKEND_ENTRYPOINT_GROUP):
        if entry_point.name == name:
            plugin_class = entry_point.load()
            if not issubclass(plugin_class, SecretManagerPlugin):
                raise TypeError(f"Backend '{name}' must inherit from SecretManagerPlugin")
            return plugin_class
    raise LookupError(f"Unknown backend '{name}'")
