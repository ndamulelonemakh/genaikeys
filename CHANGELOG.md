# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0rc3] - Unreleased

### Added
- Context manager protocol on `GenAIKeys`: `with GenAIKeys.azure() as sk: ...` automatically clears cached secrets on exit (#9).
- Stronger redaction guarantee: backend exception messages are no longer interpolated into log records — only the exception type is logged, so a misbehaving backend cannot leak a secret value via logs (#10).
- Regression test asserting per-instance cache isolation across backends.

### Changed
- **BREAKING:** `GenAIKeys` is no longer a singleton. Each call to `GenAIKeys(...)` (and the `azure()`/`aws()`/`gcp()`/`backend()` factories) now returns a fresh instance with its own private cache. This eliminates the cross-backend cache collision where a second `GenAIKeys.aws()` call would return the cached value of an earlier `GenAIKeys.azure()` call for the same secret name (#12, #15).
- `SingletonMeta` is no longer exported from the package.

### Removed
- `SingletonMeta` metaclass on `GenAIKeys`.
- Stray `del os.environ[secret_name]` call inside `invalidate_cache` (dead code).

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
