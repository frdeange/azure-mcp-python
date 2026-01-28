"""Tests for CredentialProvider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from azure_mcp.core.auth import CredentialProvider, get_default_credential


class TestCredentialProvider:
    """Tests for CredentialProvider class."""

    def setup_method(self):
        """Clear credential cache before each test."""
        CredentialProvider.clear_cache()

    def test_get_credential_returns_chained_credential(self):
        """Test that get_credential returns a ChainedTokenCredential."""
        with patch("azure_mcp.core.auth.ChainedTokenCredential") as mock_chain:
            mock_cred = MagicMock()
            mock_chain.return_value = mock_cred

            result = CredentialProvider.get_credential()

            assert result == mock_cred
            mock_chain.assert_called_once()

    def test_get_credential_includes_managed_identity(self):
        """Test that credential chain includes ManagedIdentityCredential."""
        with (
            patch("azure_mcp.core.auth.ManagedIdentityCredential") as mi_mock,
            patch("azure_mcp.core.auth.EnvironmentCredential"),
            patch("azure_mcp.core.auth.VisualStudioCodeCredential"),
            patch("azure_mcp.core.auth.AzureCliCredential"),
            patch("azure_mcp.core.auth.ChainedTokenCredential") as chain_mock,
        ):
            CredentialProvider.get_credential()

            # ManagedIdentityCredential should be instantiated
            mi_mock.assert_called_once()
            # ChainedTokenCredential should receive 4 credentials
            assert chain_mock.call_count == 1
            args = chain_mock.call_args[0]
            assert len(args) == 4

    def test_get_credential_with_tenant(self):
        """Test credential with explicit tenant."""
        with (
            patch("azure_mcp.core.auth.EnvironmentCredential") as env_mock,
            patch("azure_mcp.core.auth.ManagedIdentityCredential"),
            patch("azure_mcp.core.auth.VisualStudioCodeCredential") as vsc_mock,
            patch("azure_mcp.core.auth.AzureCliCredential") as cli_mock,
            patch("azure_mcp.core.auth.ChainedTokenCredential"),
        ):
            CredentialProvider.get_credential(tenant_id="test-tenant")

            # Tenant-aware credentials should receive tenant_id
            env_mock.assert_called_once_with(tenant_id="test-tenant")
            vsc_mock.assert_called_once_with(tenant_id="test-tenant")
            cli_mock.assert_called_once_with(tenant_id="test-tenant")

    def test_get_credential_caches_result(self):
        """Test that credentials are cached."""
        with patch("azure_mcp.core.auth.ChainedTokenCredential") as mock_chain:
            mock_cred = MagicMock()
            mock_chain.return_value = mock_cred

            result1 = CredentialProvider.get_credential()
            result2 = CredentialProvider.get_credential()

            assert result1 is result2
            # Should only create once
            mock_chain.assert_called_once()

    def test_clear_cache(self):
        """Test that clear_cache removes cached credentials."""
        with patch("azure_mcp.core.auth.ChainedTokenCredential") as mock_chain:
            mock_cred = MagicMock()
            mock_chain.return_value = mock_cred

            CredentialProvider.get_credential()
            CredentialProvider.clear_cache()
            CredentialProvider.get_credential()

            # Should create twice after cache clear
            assert mock_chain.call_count == 2

    def test_user_assigned_identity_uses_client_id(self):
        """Test that AZURE_CLIENT_ID env var is used for user-assigned identity."""
        with (
            patch.dict("os.environ", {"AZURE_CLIENT_ID": "my-client-id"}),
            patch("azure_mcp.core.auth.ManagedIdentityCredential") as mi_mock,
            patch("azure_mcp.core.auth.EnvironmentCredential"),
            patch("azure_mcp.core.auth.VisualStudioCodeCredential"),
            patch("azure_mcp.core.auth.AzureCliCredential"),
            patch("azure_mcp.core.auth.ChainedTokenCredential"),
        ):
            CredentialProvider.get_credential()

            mi_mock.assert_called_once_with(client_id="my-client-id")
