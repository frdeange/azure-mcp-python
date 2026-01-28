"""Azure authentication utilities.

Provides credential chain management with caching and multi-tenant support.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING

from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    EnvironmentCredential,
    ManagedIdentityCredential,
    VisualStudioCodeCredential,
)

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential


class CredentialProvider:
    """
    Provides Azure credentials with automatic fallback chain.

    Respects AZURE_TOKEN_CREDENTIALS environment variable:
    - "dev": Development credentials (CLI, VS Code)
    - "prod": Production credentials (Managed Identity, Environment)
    - Not set: Development chain (default)

    Credentials are cached per tenant to avoid repeated auth flows.
    """

    _credentials: dict[str, TokenCredential] = {}

    @classmethod
    def get_credential(cls, tenant_id: str | None = None) -> TokenCredential:
        """
        Get a credential, optionally scoped to a specific tenant.

        Args:
            tenant_id: Optional tenant ID to scope the credential to.

        Returns:
            A TokenCredential instance for Azure authentication.
        """
        cache_key = tenant_id or "default"

        if cache_key not in cls._credentials:
            cls._credentials[cache_key] = cls._create_credential(tenant_id)

        return cls._credentials[cache_key]

    @classmethod
    def _create_credential(cls, tenant_id: str | None = None) -> TokenCredential:
        """Create a new credential chain based on environment configuration."""
        mode = os.environ.get("AZURE_TOKEN_CREDENTIALS", "dev").lower()

        if mode == "prod":
            return cls._create_production_chain(tenant_id)
        else:
            return cls._create_development_chain(tenant_id)

    @classmethod
    def _create_development_chain(cls, tenant_id: str | None = None) -> TokenCredential:
        """Create credential chain for development environments."""
        kwargs: dict[str, str] = {}
        if tenant_id:
            kwargs["tenant_id"] = tenant_id

        credentials: list[TokenCredential] = [
            EnvironmentCredential(**kwargs),
            VisualStudioCodeCredential(**kwargs),
            AzureCliCredential(**kwargs),
        ]

        return ChainedTokenCredential(*credentials)

    @classmethod
    def _create_production_chain(cls, tenant_id: str | None = None) -> TokenCredential:
        """Create credential chain for production environments."""
        kwargs: dict[str, str] = {}
        if tenant_id:
            kwargs["tenant_id"] = tenant_id

        # Check for user-assigned managed identity
        client_id = os.environ.get("AZURE_CLIENT_ID")
        mi_kwargs: dict[str, str] = {}
        if client_id:
            mi_kwargs["client_id"] = client_id

        credentials: list[TokenCredential] = [
            EnvironmentCredential(**kwargs),
            ManagedIdentityCredential(**mi_kwargs),
        ]

        return ChainedTokenCredential(*credentials)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached credentials."""
        cls._credentials.clear()


@lru_cache(maxsize=1)
def get_default_credential() -> TokenCredential:
    """Get the default credential (cached)."""
    return CredentialProvider.get_credential()
