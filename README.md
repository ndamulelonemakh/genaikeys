# GenAIKeys

GenAIKeys is a Python library that streamlines API key management for Generative AI applications by securely
storing the keys in cloud secret vaults like [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/),
[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), and [Google Secret Manager](https://cloud.google.com/secret-manager).

[![PyPI version](https://badge.fury.io/py/genaikeys.svg)](https://badge.fury.io/py/genaikeys)
[![CI](https://github.com/ndamulelonemakh/genaikeys/actions/workflows/ci.yml/badge.svg)](https://github.com/ndamulelonemakh/genaikeys/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Features

- Secure API key management for GenAI services — no hard-coded credentials
- Built-in support for OpenAI, Anthropic, and Google Gemini convenience methods
- In-memory caching with configurable TTL to minimise vault API calls
- Extensible package layout with public `plugins` and `backends` subpackages
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
from genaikeys import GenAIKeys

# Azure Key Vault
sk = GenAIKeys.azure()

# Retrieve any secret by name
api_key = sk.get("huggingface-api-key")

# Convenience methods for popular AI providers
openai_key    = sk.get_openai_key()     # looks up "OPENAI-API-KEY" in the vault
anthropic_key = sk.get_anthropic_key()  # looks up "ANTHROPIC-API-KEY"
gemini_key    = sk.get_gemini_key()     # looks up "GEMINI-API-KEY"
```

> **Note on secret names:** Azure Key Vault does not allow underscores in secret names.
> GenAIKeys automatically converts `_` → `-` when querying Azure, so store your secret
> as `OPENAI-API-KEY` in the vault and retrieve it with `sk.get("OPENAI_API_KEY")` or
> `sk.get_openai_key()`.

---

## Authentication

### Azure Key Vault

**Required configuration:**

| Environment variable | Description |
|---|---|
| `AZURE_KEY_VAULT_URL` | Full URL of your vault, e.g. `https://my-vault.vault.azure.net/` |
| `MANAGED_IDENTITY_CLIENT_ID` | *(Optional)* Client ID of a User-Assigned Managed Identity |

GenAIKeys uses [`DefaultAzureCredential`](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential),
which tries the following credential sources **in order** until one succeeds:

1. `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID` environment variables (service principal)
2. Workload identity (Kubernetes)
3. Managed Identity (Azure VMs, App Service, Container Apps, AKS)
4. Azure CLI (`az login`)
5. Azure PowerShell (`Connect-AzAccount`)
6. Azure Developer CLI (`azd auth login`)

**RBAC requirement:** The identity used must have the **Key Vault Secrets User** role on the vault (or `Key Vault Secrets Officer` if you also need to create/update secrets).

**Local development:**
```bash
az login
export AZURE_KEY_VAULT_URL="https://my-vault.vault.azure.net/"
```

**Managed Identity (e.g. Azure App Service):**
```bash
# System-assigned MI — no extra vars needed beyond AZURE_KEY_VAULT_URL
export AZURE_KEY_VAULT_URL="https://my-vault.vault.azure.net/"

# User-assigned MI
export AZURE_KEY_VAULT_URL="https://my-vault.vault.azure.net/"
export MANAGED_IDENTITY_CLIENT_ID="<your-client-id>"
```

**Service principal (CI/CD):**
```bash
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_ID="<client-id>"
export AZURE_CLIENT_SECRET="<client-secret>"
export AZURE_KEY_VAULT_URL="https://my-vault.vault.azure.net/"
```

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.azure(vault_url="https://my-vault.vault.azure.net/")
key = sk.get("OPENAI_API_KEY")
```

---

### AWS Secrets Manager

**Required configuration:**

| Environment variable | Description |
|---|---|
| `AWS_DEFAULT_REGION` | AWS region where your secrets are stored, e.g. `us-east-1` |

GenAIKeys uses [`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html),
which resolves credentials from the standard
[AWS credential provider chain](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html):

1. `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` environment variables
2. AWS credentials file (`~/.aws/credentials`)
3. AWS config file (`~/.aws/config`)
4. IAM role attached to the compute resource (EC2, Lambda, ECS task, etc.)
5. AWS SSO (`aws sso login`)

**IAM requirement:** The identity used must have at minimum the `secretsmanager:GetSecretValue` action on the target secrets. For `list_secrets()` / `exists()` you also need `secretsmanager:ListSecrets`.

**Local development:**
```bash
aws configure   # or: aws sso login
export AWS_DEFAULT_REGION="us-east-1"
```

**IAM role (Lambda, EC2, ECS):**
```bash
# No credential env vars needed — attach the IAM role to your resource
export AWS_DEFAULT_REGION="us-east-1"
```

**Service account / CI (access key):**
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
```

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.aws(region_name="us-east-1")
key = sk.get("OPENAI_API_KEY")
```

---

### Google Secret Manager

**Required configuration:**

| Environment variable | Description |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID where your secrets live |

GenAIKeys uses the [Google Cloud Python SDK](https://cloud.google.com/python/docs/reference/secretmanager/latest),
which resolves credentials via
[Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials):

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to a service account key file
2. Attached service account on GCE, GKE, Cloud Run, App Engine, Cloud Functions
3. `gcloud` CLI (`gcloud auth application-default login`)

**IAM requirement:** The service account (or user) must have the **Secret Manager Secret Accessor** role (`roles/secretmanager.secretAccessor`) on the project or individual secrets.

**Local development:**
```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
```

**Attached service account (Cloud Run, GKE Workload Identity, etc.):**
```bash
# No credential files needed — configure the SA on the resource
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
```

**Service account key file (CI/CD):**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
```

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.gcp(project_id="my-gcp-project")
key = sk.get("OPENAI_API_KEY")
```

---

## Caching

Secrets are cached in-process for `cache_duration` seconds (default `3600`). To tune:

```python
sk = GenAIKeys.azure(cache_duration=300)   # 5-minute TTL

# Invalidate a single key
sk.clear("OPENAI_API_KEY")

# Invalidate everything
sk.clear()
```

---

## Custom Backend

Implement `SecretManagerPlugin` to add any secret store:

```python
from genaikeys import GenAIKeys
from genaikeys.plugins import SecretManagerPlugin

class MyPlugin(SecretManagerPlugin):
    def get_secret(self, secret_name: str) -> str:
        # your retrieval logic here
        return "my-secret-value"

sk = GenAIKeys(MyPlugin())
```

Bundled backends also live in explicit public modules:

```python
from genaikeys.backends.aws import AWSSecretsManagerPlugin
from genaikeys.backends.azure import AzureKeyVaultPlugin
from genaikeys.backends.gcp import GCPSecretManagerPlugin
```

Third-party packages can register additional backends under the `genaikeys.backends`
entry-point group and instantiate them through `GenAIKeys.backend("name", **kwargs)`.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
