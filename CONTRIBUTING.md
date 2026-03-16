# Contributing to GenAIKeys

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/ndamulelonemakh/genaikeys.git
cd genaikeys

# Install with dev dependencies (Poetry)
poetry install --with dev

# Or plain pip
pip install -e ".[all]"
pip install pytest pytest-cov ruff
```

## Running Tests

```bash
pytest
# With coverage
pytest --cov=genaikeys --cov-report=term-missing
```

The test suite uses mocks — no live cloud credentials are required.

## Linting

```bash
ruff check genaikeys/
```

## Pull Requests

1. Fork the repository and create a feature branch from `main`.
2. Add tests for any new behaviour.
3. Ensure `pytest` and `ruff check` both pass before opening a PR.
4. Keep commits focused and write clear commit messages.

## Reporting Issues

Please use [GitHub Issues](https://github.com/ndamulelonemakh/genaikeys/issues).
For security vulnerabilities, see [SECURITY.md](SECURITY.md) if present, or email the maintainer directly.
