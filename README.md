# GenAIKeys [WIP]

GenAIKeys is a Python library that streamlines API key management for Generative AI applications by securely
storing the keys in cloud secret vaults like [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/), 
[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), and [Google Secret Manager](https://cloud.google.com/secret-manager).

> **Disclaimer**: Please exercise caution when using this package in production environments. We recommend that you
> review the codebase and ensure that it meets your security requirements before deploying it in a production environment.

[![PyPI version](https://badge.fury.io/py/genaikeys.svg)](https://badge.fury.io/py/genaikeys)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔐 Secure API key management for GenAI services
- 🚀 Zero environment variable configuration
- ⚡️ Direct integration with cloud secret vaults
- 🔌 Built-in support for OpenAI, Anthropic, and Google Gemini
- 🛠 Extensible architecture for custom secret backends

## Installation

```bash
pip install genaikeys
```

## Quick Start

```python
from genaikeys import SecretKeeper

# Initialize GenAIKeys
skp = SecretKeeper.from_defaults()

# Get API keys directly
api_key = skp.get('huggingface-api-key')

# Use convenience methods
openai_key = skp.get_openai_key()
anthropic_key = skp.get_anthropic_key()
gemini_key = skp.get_gemini_key()
```

## Configuration

* By default, GenAIKeys uses the `Azure Key Vault` secret backend. You can configure the secret backend by setting
  the `SECRET_KEEPER_BACKEND` environment variable to one of the following values:
    - `AZURE`
    - `AWS`
    - `GCP`
* We recommend setting the `SECRET_KEEPER_BACKEND` environment variable in a persistent configuration file like
  `.bashrc` or `.zshrc`.*

* You will also need to provide the configurations for the secret backend you choose.

#### Azure Key Vault

- The following environment variables are required for the `Azure Key Vault` secret backend:
    - `AZURE_KEY_VAULT_URL`
- Optionally you can also provide the following environment variables:
    - `MANGED_IDENTITY_CLIENT_ID` (for User Assigned Managed Identity authentication)

#### AWS Secrets Manager [WIP]

#### Google Secret Manager [WIP]

## Documentation

For detailed usage instructions, API reference, and advanced configuration options, visit
our [documentation](https://docs.GenAIKeys.dev).

## Contributing

We welcome contributions! Please see our [contribution guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
