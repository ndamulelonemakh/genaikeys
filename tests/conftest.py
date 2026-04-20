import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_cloud_backends():
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
    ]

    for mod in _backend_modules:
        sys.modules.pop(mod, None)

    with patch.dict(sys.modules, cloud_stubs):
        yield

    for mod in _backend_modules:
        sys.modules.pop(mod, None)
