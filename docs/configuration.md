# Configuration

Each cloud backend requires specific environment variables for authentication.
GenAIKeys uses **keyless authentication** exclusively — no API keys or passwords
are stored in code.

---

## Azure Key Vault

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.azure()
sk = GenAIKeys.azure(vault_url="https://my-vault.vault.azure.net/")
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_KEY_VAULT_URL` | Yes | Full URL of your vault |
| `MANAGED_IDENTITY_CLIENT_ID` | No | Client ID for User-Assigned Managed Identity |
| `GENAIKEYS_DEBUG` | No | Enable debug logging (`true`/`false`) |

### Credential Chain

GenAIKeys uses [`DefaultAzureCredential`](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential), which tries these sources in order:

1. Environment variables (`AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID`)
2. Workload Identity (Kubernetes)
3. Managed Identity (VMs, App Service, Container Apps, AKS)
4. Azure CLI (`az login`)
5. Azure PowerShell
6. Azure Developer CLI

**RBAC requirement:** The identity must have **Key Vault Secrets User** role on the vault.

### Secret Name Normalization

Azure Key Vault does not allow underscores in secret names. GenAIKeys automatically
converts `_` → `-` when querying, so `sk.get("OPENAI_API_KEY")` looks up `OPENAI-API-KEY`.

---

## AWS Secrets Manager

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.aws()
sk = GenAIKeys.aws(region_name="us-east-1")
# Or with SSO profile:
sk = GenAIKeys.aws(region_name="us-east-1", profile_name="my-sso")
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_DEFAULT_REGION` | Yes | AWS region where secrets are stored |
| `AWS_PROFILE` | No | SSO / named profile from `~/.aws/config` |

### Credential Chain

Uses the standard [boto3 credential chain](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html):

1. Environment variables (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. AWS config file (`~/.aws/config`)
4. IAM role (EC2, Lambda, ECS, EKS)
5. AWS SSO (`aws sso login`)

**IAM requirement:** `secretsmanager:GetSecretValue` on target secrets. For `exists()` / `list_secrets()`, also `secretsmanager:ListSecrets`.

---

## Google Secret Manager

```python
from genaikeys import GenAIKeys

sk = GenAIKeys.gcp()
sk = GenAIKeys.gcp(project_id="my-gcp-project")
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | GCP project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to service account key file |

### Credential Chain

Uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials):

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. Attached service account (GCE, GKE, Cloud Run, Cloud Functions)
3. `gcloud auth application-default login`

**IAM requirement:** `roles/secretmanager.secretAccessor` on the project or individual secrets.

---

## Caching

All backends use in-memory caching with a configurable TTL (default: 3600 seconds):

```python
sk = GenAIKeys.azure(cache_duration=300)  # 5-minute TTL

sk.clear("OPENAI_API_KEY")  # Invalidate one key
sk.clear()                   # Invalidate all
```

## Bulk fetch

```python
keys = sk.get_many(["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"])
# {"OPENAI_API_KEY": "...", "ANTHROPIC_API_KEY": "...", "GEMINI_API_KEY": "..."}
```

Cached entries are reused; only misses hit the backend.

## Async API

Every backend exposes an `async` surface via `asyncio.to_thread`:

```python
async with GenAIKeys.azure() as sk:
    key = await sk.aget("OPENAI_API_KEY")
    bundle = await sk.aget_many(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])
```

Cache hits short-circuit without dispatching to a worker thread. `aget_many`
fans out across the default thread pool — for very large batches, configure
`loop.set_default_executor` with a sized `ThreadPoolExecutor`.

## Environment-variable fallback (local development)

Pass `fallback_env=True` to fall back to `os.environ` when the backend lookup
fails. A `WARNING` is logged whenever the fallback is used so the masking is
observable.

```python
sk = GenAIKeys.azure(fallback_env=True)
sk.get("OPENAI_API_KEY")  # tries vault, then os.environ["OPENAI_API_KEY"]
```

The fallback is **off by default** — production code should rely on the vault.

## Logging

The package logger is silent by default. For local debugging:

```python
from genaikeys import disable_logging, enable_logging

enable_logging(level="DEBUG")
disable_logging()
```
