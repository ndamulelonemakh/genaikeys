# GenAIKeys

Secure API key management for Generative AI applications, backed by
[Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/),
[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), and
[Google Secret Manager](https://cloud.google.com/secret-manager).

## Why GenAIKeys?

- **One API across clouds** — swap providers without touching application code.
- **Keyless authentication by default** — Managed Identity, IAM roles, ADC.
- **Built-in TTL cache** — fewer vault calls, lower bills.
- **Convenience helpers** for OpenAI, Anthropic, and Gemini keys.
- **Pluggable** — bring your own backend in a few lines.

## Install

```bash
pip install genaikeys              # Azure (default)
pip install "genaikeys[aws]"
pip install "genaikeys[gcp]"
pip install "genaikeys[all]"
```

## Quick start

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.azure()
api_key = sk.get_openai_key()
```

## Documentation

- [Configuration & authentication](configuration.md) — per-provider setup for Azure, AWS, GCP.
- [CLI](cli.md) — populate `.env` files from a vault.
- [Custom backends](custom-backends.md) — implement your own secret store.
- [Logging](logging.md) — enable, disable, route to a custom handler.

## Project links

- [GitHub repository](https://github.com/ndamulelonemakh/genaikeys)
- [PyPI package](https://pypi.org/project/genaikeys/)
- [Changelog](https://github.com/ndamulelonemakh/genaikeys/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/ndamulelonemakh/genaikeys/blob/main/CONTRIBUTING.md)
