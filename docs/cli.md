# CLI

GenAIKeys ships with a small CLI for common automation tasks.

## `genaikeys fill`

Populate a `.env` (or `.env.example`) file with values pulled from a secret vault.

```bash
genaikeys fill .env --keyvault https://my-kv.vault.azure.net
```

By default, only keys with **empty values** are filled; existing values are kept untouched. Comments and blank lines are preserved.

### Options

| Flag | Description |
| --- | --- |
| `--backend {azure,aws,gcp}` | Secret backend to use (default: `azure`). |
| `--keyvault URL` | Azure Key Vault URL. Implies `--backend azure`. |
| `--region`, `--profile` | AWS region and profile (when `--backend aws`). |
| `--project-id` | GCP project id (when `--backend gcp`). |
| `--output PATH` | Write to `PATH` instead of editing the source file in place. |
| `--overwrite` | Replace existing values instead of skipping them. |
| `--dry-run` | Print the rendered file to stdout; do not write. |
| `--strict` | Exit with a non-zero status if any key is missing in the vault. |

### Example

Given `.env.example`:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
APP_ENV=local
```

Running:

```bash
genaikeys fill .env.example --keyvault https://my-kv.vault.azure.net --output .env
```

Produces `.env` with the two API keys populated from the vault while leaving `APP_ENV` unchanged. Keys that are not present in the vault are reported on stderr and left as-is (use `--strict` to fail the command in that case).

### Authentication

The CLI uses the same backend authentication as the Python API — see [Configuration & authentication](configuration.md).

## `genaikeys push`

Upload values from a local `.env` file into a secret vault — the inverse of `fill`.

```bash
genaikeys push .env --keyvault https://my-kv.vault.azure.net
```

By default, existing secrets in the vault are **not** overwritten; pass `--overwrite` to replace them. Empty and commented-out keys are ignored.

### Options

| Flag | Description |
| --- | --- |
| `--backend {azure,aws,gcp}` | Secret backend to use (default: `azure`). |
| `--keyvault URL` | Azure Key Vault URL. Implies `--backend azure`. |
| `--region`, `--profile` | AWS region and profile (when `--backend aws`). |
| `--project-id` | GCP project id (when `--backend gcp`). |
| `--only K1,K2` | Only push the listed keys. |
| `--overwrite` | Overwrite secrets that already exist in the vault. |
| `--dry-run` | List what would be pushed without calling the backend. |

> **Note on Azure Key Vault:** names containing `_` are normalized to `-` on upload, matching the lookup behaviour of `fill`.
