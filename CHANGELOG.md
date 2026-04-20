# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-20

First GA release.

### Added
- `SECURITY.md` with responsible disclosure policy
- `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)
- GitHub issue templates (bug report, feature request) and PR template
- `.github/CODEOWNERS` for automated review assignment
- `.github/dependabot.yml` for automated dependency updates
- `.pre-commit-config.yaml` with ruff lint, ruff format, and standard hooks
- `tox.ini` for multi-Python testing (3.10, 3.11, 3.12)
- `poetry.toml` for consistent local development
- `.vscode/settings.json` with format-on-save and ruff integration
- `docs/` folder with configuration guide and custom backend documentation
- `mypy` type checking in CI pipeline
- `ruff format --check` enforcement in CI pipeline
- Coverage threshold (80%) in pytest configuration
- Additional tests for error handling and plugin interface

### Changed
- Bumped version from 0.1.0 to 1.0.0

## [0.1.0] - 2026-03-16

First stable release.

### Added
- Azure Key Vault, AWS Secrets Manager, and Google Secret Manager backends
- In-memory caching with configurable TTL and thread-safe invalidation
- Singleton `SecretKeeper` with convenience methods for OpenAI, Anthropic, and Gemini
- Extensible `SecretManagerPlugin` base class for custom backends
- Unit test suite covering caching, singleton, thread-safety, and all factory methods
- CI workflow (`.github/workflows/ci.yml`) running tests on Python 3.10–3.12
- Publish workflow now requires tests to pass before building

### Fixed
- Broken import in `_azure_keyvault.py` (`._secret_manager` → `.types`)
- Typo `MANGED_IDENTITY_CLIENT_ID` → `MANAGED_IDENTITY_CLIENT_ID`
- `get_secret` no longer leaks secret values into `os.environ`
- GCP module replaced `print()` error output with proper `logging`
