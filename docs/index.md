# GenAIKeys Documentation

GenAIKeys is a Python library that streamlines API key management for Generative AI
applications by securely retrieving secrets from cloud vaults.

## Overview

- **Secure by default** — uses keyless authentication (Managed Identity, IAM roles, ADC)
- **Multi-cloud** — Azure Key Vault, AWS Secrets Manager, Google Secret Manager
- **Cached** — in-memory TTL cache to minimise vault API calls
- **Extensible** — plugin interface for custom backends
- **Thread-safe** — singleton with locked cache

## Quick Start

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.azure()
key = sk.get("OPENAI_API_KEY")
```

## Documentation

- [Configuration](configuration.md) — per-provider authentication setup
- [Custom Backends](custom-backends.md) — implementing your own secret provider

## Links

- [GitHub Repository](https://github.com/ndamulelonemakh/genaikeys)
- [PyPI Package](https://pypi.org/project/genaikeys/)
- [CHANGELOG](../CHANGELOG.md)
- [CONTRIBUTING](../CONTRIBUTING.md)
