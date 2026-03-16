# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
