# GenAIKeys

[![PyPI version](https://badge.fury.io/py/genaikeys.svg)](https://badge.fury.io/py/genaikeys)
[![CI](https://github.com/ndamulelonemakh/genaikeys/actions/workflows/ci.yml/badge.svg)](https://github.com/ndamulelonemakh/genaikeys/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

> Convenient, extensible API key management for Generative AI applications using cloud secret vaults.
> One Python API across **Azure Key Vault**, **AWS Secrets Manager**, and **Google Secret Manager**.

```mermaid
flowchart LR
    App[Your AI App] -->|sk.get()| Cache{TTL Cache}
    
    subgraph GenAIKeys
        Cache
    end
    
    Cache -->|Cache miss| Azure[(Azure Key Vault)]
    Cache -->|Cache miss| AWS[(AWS Secrets)]
    Cache -->|Cache miss| GCP[(GCP Secret Manager)]
```

## Why GenAIKeys?

- **One API, three clouds** — swap providers without touching app code.
- **Keyless by default** — Managed Identity, IAM roles, ADC.
- **TTL cache built in** — fewer vault calls, lower bills.
- **Convenience helpers** for OpenAI, Anthropic, and Gemini.
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

sk = GenAIKeys.azure()                  # or .aws() / .gcp()

api_key       = sk.get("huggingface-api-key")
openai_key    = sk.get_openai_key()     # → "OPENAI-API-KEY"
anthropic_key = sk.get_anthropic_key()  # → "ANTHROPIC-API-KEY"
gemini_key    = sk.get_gemini_key()     # → "GEMINI-API-KEY"
```

Factory methods read defaults from the environment:

| Backend | Env var(s) |
|---|---|
| `GenAIKeys.azure()` | `AZURE_KEY_VAULT_URL` |
| `GenAIKeys.aws()`   | `AWS_DEFAULT_REGION`, optional `AWS_PROFILE` |
| `GenAIKeys.gcp()`   | `GOOGLE_CLOUD_PROJECT` |

> **Azure tip:** Key Vault disallows underscores in secret names. GenAIKeys auto-converts
> `_` → `-`, so `sk.get("OPENAI_API_KEY")` looks up `OPENAI-API-KEY`.

Working examples for each cloud live in [`examples/`](examples/).

## Documentation

Full docs are published at **<https://ndamulelonemakh.github.io/genaikeys/>**:

- [Configuration & authentication](docs/configuration.md) — Azure, AWS, GCP setup, credential chains, IAM/RBAC requirements.
- [Custom backends](docs/custom-backends.md) — implement your own secret store.
- [Logging](docs/logging.md) — enable, disable, route to a custom handler.

## Caching at a glance

```python
sk = GenAIKeys.azure(cache_duration=300)   # 5-minute TTL
sk.clear("OPENAI_API_KEY")                 # invalidate one key
sk.clear()                                 # invalidate everything
```

## Custom backend in 10 lines

```python
from genaikeys import GenAIKeys
from genaikeys.plugins import SecretManagerPlugin

class MyPlugin(SecretManagerPlugin):
    def get_secret(self, secret_name: str) -> str:
        return "my-secret-value"

sk = GenAIKeys(MyPlugin())
```

See [Custom backends](docs/custom-backends.md) for the full interface and entry-point registration.

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
