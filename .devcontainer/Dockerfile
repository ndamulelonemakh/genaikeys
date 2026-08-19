FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install Astral uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set security environment variables to prevent keychain/keyring access in container
ENV PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-managed

# Switch to non-root vscode user
USER vscode

WORKDIR /workspace
