"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import Any, AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest

from azure_mcp.core.auth import CredentialProvider
from azure_mcp.core.cache import cache
from azure_mcp.core.registry import registry


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before each test."""
    registry.clear()
    yield
    registry.clear()


@pytest.fixture
def mock_credential():
    """Create a mock Azure credential."""
    credential = MagicMock()
    credential.get_token.return_value = MagicMock(
        token="test-token",
        expires_on=9999999999,
    )
    return credential


@pytest.fixture
def mock_subscription_client(mock_credential):
    """Create a mock subscription client."""
    from unittest.mock import MagicMock

    mock_sub = MagicMock()
    mock_sub.subscription_id = "test-subscription-id"
    mock_sub.display_name = "Test Subscription"
    mock_sub.state = MagicMock(value="Enabled")
    mock_sub.tenant_id = "test-tenant-id"

    client = MagicMock()
    client.subscriptions.list.return_value = [mock_sub]

    return client


@pytest.fixture
def mock_resourcegraph_client(mock_credential):
    """Create a mock Resource Graph client."""
    from unittest.mock import MagicMock

    client = MagicMock()

    result = MagicMock()
    result.data = []
    result.count = 0
    result.total_records = 0
    result.skip_token = None
    result.result_truncated = False

    client.resources.return_value = result

    return client


@pytest.fixture
def patch_credential(mock_credential):
    """Patch credential provider to return mock credential."""
    with patch.object(
        CredentialProvider, "get_credential", return_value=mock_credential
    ):
        yield mock_credential
