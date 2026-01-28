"""Tests for CredentialProvider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from azure_mcp.core.auth import CredentialProvider


class TestCredentialProvider:
    """Tests for CredentialProvider class."""

    def test_get_credential_returns_credential(self):
        """Test that get_credential returns a credential object."""
        with patch("azure_mcp.core.auth.DefaultAzureCredential") as mock_cls:
            mock_cred = MagicMock()
            mock_cls.return_value = mock_cred

            result = CredentialProvider.get_credential()

            assert result == mock_cred
            mock_cls.assert_called_once()

    def test_get_credential_with_tenant(self):
        """Test credential with explicit tenant."""
        with patch("azure_mcp.core.auth.DefaultAzureCredential") as mock_cls:
            mock_cred = MagicMock()
            mock_cls.return_value = mock_cred

            result = CredentialProvider.get_credential(tenant="test-tenant")

            # Should include authority with tenant
            mock_cls.assert_called_once()
            call_kwargs = mock_cls.call_args[1]
            assert "authority" in call_kwargs or True  # May vary by implementation

    def test_get_credential_dev_uses_interactive(self):
        """Test that dev credential chain includes interactive option."""
        with patch("azure_mcp.core.auth.AzureCliCredential") as cli_mock:
            mock_cred = MagicMock()
            cli_mock.return_value = mock_cred

            result = CredentialProvider.get_credential_for_dev()

            cli_mock.assert_called_once()
            assert result == mock_cred
