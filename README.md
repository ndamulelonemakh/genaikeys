# GenAIKeys

GenAIKeys is a Python library that streamlines API key management for Generative AI applications by securely
storing the keys in cloud secret vaults like [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/),
[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), and [Google Secret Manager](https://cloud.google.com/secret-manager).

[![PyPI version](https://badge.fury.io/py/genaikeys.svg)](https://badge.fury.io/py/genaikeys)
[![CI](https://github.com/ndamulelonemakh/genaikeys/actions/workflows/ci.yml/badge.svg)](https://github.com/ndamulelonemakh/genaikeys/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Features

- Secure API key management for GenAI services
- Zero hard-coded credentials — keys are read from cloud vaults at runtime
- Built-in support for OpenAI, Anthropic, and Google Gemini convenience methods
- In-memory caching with configurable TTL to minimise vault API calls
- Extensible plugin architecture for custom secret backends
- Thread-safe by design

## Installation

```bash
# Azure (default)
pip install genaikeys

# AWS
pip install "genaikeys[aws]"

# GCP
pip install "genaikeys[gcp]"

# All backends
pip install "genaikeys[all]"
```

## Quick Start

```python
from genaikeys import SecretKeeper

# Azure Key Vault (requires AZURE_KEY_VAULT_URL env var)
skp = SecretKeeper.azure()

# Retrieve any secret by name
api_key = skp.get("huggingface-api-key")

# Convenience methods for popular AI providers
openai_key  = skp.get_openai_key()    # looks up "OPENAI_API_KEY"
anthropic_key = skp.get_anthropic_key()  # looks up "ANTHROPIC_API_KEY"
gemini_key  = skp.get_gemini_key()    # looks up "GEMINI_API_KEY"
```

## Configuration

### Azure Key Vault

```bash
export AZURE_KEY_VAULT_URL="https://my-vault.vault.azure.net/"
# Optional — only needed for User-Assigned Managed Identity
export MANAGED_IDENTITY_CLIENT_ID="<client-id>"
```

```python
from genaikeys import SecretKeeper

sk = SecretKeeper.azure(vault_url="https://my-vault.vault.azure.net/")
key = sk.get("OPENAI_API_KEY")
```

Authentication uses [DefaultAzureCredential](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential),
which works with Managed Identity, environment variables, `az login`, and more.

### AWS Secrets Manager

```bash
export AWS_DEFAULT_REGION="us-east-1"
# Standard AWS credential env vars (AWS_ACCESS_KEY_ID, etc.) or IAM role
```

```python
from genaikeys import SecretKeeper

sk = SecretKeeper.aws(region_name="us-east-1")
key = sk.get("OPENAI_API_KEY")
```

### Google Secret Manager

```bash
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
# Standard GCP credential setup (GOOGLE_APPLICATION_CREDENTIALS or ADC)
```

```python
from genaikeys import SecretKeeper

sk = SecretKeeper.gcp(project_id="my-gcp-project")
key = sk.get("OPENAI_API_KEY")
```

## Caching

Secrets are cached in-process for `cache_duration` seconds (default 3600). To tune:

```python
sk = SecretKeeper.azure(cache_duration=300)   # 5-minute TTL

# Invalidate a single key
sk.clear("OPENAI_API_KEY")

# Invalidate everything
sk.clear()
```

## Custom Backend

Implement `SecretManagerPlugin` to add any secret store:

```python
from genaikeys import SecretKeeper, SecretManagerPlugin

class MyPlugin(SecretManagerPlugin):
    def get_secret(self, secret_name: str) -> str:
        # your retrieval logic here
        return "my-secret-value"

sk = SecretKeeper(MyPlugin())
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
