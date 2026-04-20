"""
Pytest configuration and shared fixtures.

The cloud SDK packages (azure-*, boto3, google-cloud-*) are optional extras and
are NOT installed in the base test environment.  The ``mock_cloud_backends``
fixture stubs them into ``sys.modules`` so that backend modules can be imported
and the pure-Python / pydantic logic can be tested without any real SDK present.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_cloud_backends():
    """Inject lightweight stubs for all cloud SDK dependencies.

    Clears cached backend modules before each test so they re-import under the
    stubbed SDK environment, and tears them down afterwards so the next test
    starts with a clean slate.
    """
    cloud_stubs = {
        "azure": MagicMock(),
        "azure.identity": MagicMock(),
        "azure.keyvault": MagicMock(),
        "azure.keyvault.secrets": MagicMock(),
        "boto3": MagicMock(),
        "google": MagicMock(),
        "google.cloud": MagicMock(),
        "google.cloud.secretmanager_v1": MagicMock(),
        "google.api_core": MagicMock(),
        "google.api_core.exceptions": MagicMock(),
    }
    _backend_modules = [
        "genaikeys.backends.azure",
        "genaikeys.backends.aws",
        "genaikeys.backends.gcp",
        "genaikeys.backends.azure",
        "genaikeys.backends.aws",
        "genaikeys.backends.gcp",
    ]

    # Remove any previously cached backend modules so they re-import cleanly.
    for mod in _backend_modules:
        sys.modules.pop(mod, None)

    with patch.dict(sys.modules, cloud_stubs):
        yield

    # Tear down: remove backend modules so subsequent tests get a fresh import.
    for mod in _backend_modules:
        sys.modules.pop(mod, None)
