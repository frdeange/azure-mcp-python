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

    The credential chain tries each authentication method in order:
    1. EnvironmentCredential - Service principal via env vars
    2. ManagedIdentityCredential - Azure Managed Identity (Container Apps, VMs, etc.)
    3. VisualStudioCodeCredential - VS Code Azure extension
    4. AzureCliCredential - Azure CLI (az login)

    This works seamlessly in both development (CLI, VS Code) and production
    (Managed Identity, Container Apps) environments.

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
        """Create a unified credential chain that works in all environments."""
        kwargs: dict[str, str] = {}
        if tenant_id:
            kwargs["tenant_id"] = tenant_id

        # Check for user-assigned managed identity
        client_id = os.environ.get("AZURE_CLIENT_ID")
        mi_kwargs: dict[str, str] = {}
        if client_id:
            mi_kwargs["client_id"] = client_id

        # Unified chain: works in both dev and production
        # Order matters: faster/more specific credentials first
        credentials: list[TokenCredential] = [
            EnvironmentCredential(**kwargs),  # Service principal (CI/CD, explicit config)
            ManagedIdentityCredential(**mi_kwargs),  # Azure Managed Identity (Container Apps, VMs)
            VisualStudioCodeCredential(**kwargs),  # VS Code (development)
            AzureCliCredential(**kwargs),  # Azure CLI (development)
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
