from importlib import import_module

__all__ = ["AWSSecretsManagerPlugin", "AzureKeyVaultPlugin", "GCPSecretManagerPlugin"]


def __getattr__(name: str):
    modules = {
        "AWSSecretsManagerPlugin": (".aws", "AWSSecretsManagerPlugin"),
        "AzureKeyVaultPlugin": (".azure", "AzureKeyVaultPlugin"),
        "GCPSecretManagerPlugin": (".gcp", "GCPSecretManagerPlugin"),
    }
    if name not in modules:
        raise AttributeError(name)
    module_name, attr_name = modules[name]
    module = import_module(module_name, __name__)
    return getattr(module, attr_name)
