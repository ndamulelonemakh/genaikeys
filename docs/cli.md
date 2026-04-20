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
