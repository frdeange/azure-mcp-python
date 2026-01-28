"""Entra ID application tools.

Provides tools for application and service principal management in Microsoft Entra ID:
- List application registrations
- Get application details
- List service principals
- Get service principal details
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.entraid.service import EntraIdService


class EntraidAppListOptions(BaseModel):
    """Options for listing Entra ID applications."""

    filter_query: str = Field(
        default="",
        description=(
            "OData filter expression (e.g., \"signInAudience eq 'AzureADMyOrg'\"). "
            "Leave empty for all applications."
        ),
    )
    search: str = Field(
        default="",
        description=(
            "Search by displayName. Partial matching supported. Leave empty for no search filter."
        ),
    )
    detail_level: Literal["summary", "full"] = Field(
        default="summary",
        description=(
            "Level of detail to return: "
            "'summary' (id, appId, displayName, signInAudience), "
            "'full' (all properties including credentials, permissions)."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of applications to return (1-999).",
    )


class EntraidAppGetOptions(BaseModel):
    """Options for getting a specific Entra ID application."""

    app_id: str = Field(
        ...,
        description=(
            "Application object ID (GUID). This is the 'id' field, NOT the 'appId' (client ID). "
            "Required."
        ),
    )
    detail_level: Literal["summary", "full"] = Field(
        default="summary",
        description=(
            "Level of detail to return: "
            "'summary' (essential fields), "
            "'full' (all properties including credentials)."
        ),
    )


class EntraidServiceprincipalListOptions(BaseModel):
    """Options for listing Entra ID service principals."""

    filter_query: str = Field(
        default="",
        description=(
            "OData filter expression (e.g., \"servicePrincipalType eq 'Application'\", "
            '"accountEnabled eq true"). '
            "Leave empty for all service principals."
        ),
    )
    search: str = Field(
        default="",
        description=(
            "Search by displayName. Partial matching supported. Leave empty for no search filter."
        ),
    )
    detail_level: Literal["summary", "full"] = Field(
        default="summary",
        description=(
            "Level of detail to return: "
            "'summary' (id, appId, displayName, servicePrincipalType, accountEnabled), "
            "'full' (all properties including credentials, tags)."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of service principals to return (1-999).",
    )


class EntraidServiceprincipalGetOptions(BaseModel):
    """Options for getting a specific Entra ID service principal."""

    sp_id: str = Field(
        ...,
        description="Service principal object ID (GUID). Required.",
    )
    detail_level: Literal["summary", "full"] = Field(
        default="summary",
        description=(
            "Level of detail to return: "
            "'summary' (essential fields), "
            "'full' (all properties including credentials)."
        ),
    )


@register_tool("entraid", "app")
class EntraidAppListTool(AzureTool):
    """Tool for listing Entra ID application registrations."""

    @property
    def name(self) -> str:
        return "entraid_app_list"

    @property
    def description(self) -> str:
        return (
            "List application registrations in Microsoft Entra ID (Azure AD). "
            "Returns app registrations owned by the organization. "
            "Use filter to narrow by signInAudience or other properties. "
            "Note: To see apps in your tenant, use entraid_serviceprincipal_list instead. "
            "Requires Application.Read.All permission."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return EntraidAppListOptions

    async def execute(self, options: EntraidAppListOptions) -> Any:
        """Execute the list applications operation."""
        service = EntraIdService()

        try:
            return await service.list_applications(
                filter_query=options.filter_query,
                search=options.search,
                detail_level=options.detail_level,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Application") from e


@register_tool("entraid", "app")
class EntraidAppGetTool(AzureTool):
    """Tool for getting a specific Entra ID application."""

    @property
    def name(self) -> str:
        return "entraid_app_get"

    @property
    def description(self) -> str:
        return (
            "Get a specific application registration from Microsoft Entra ID by object ID. "
            "Returns detailed app information including credentials, permissions, and redirect URIs. "
            "Note: Use the 'id' field (object ID), not the 'appId' (client ID). "
            "Requires Application.Read.All permission."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return EntraidAppGetOptions

    async def execute(self, options: EntraidAppGetOptions) -> Any:
        """Execute the get application operation."""
        service = EntraIdService()

        try:
            return await service.get_application(
                app_id=options.app_id,
                detail_level=options.detail_level,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Application") from e


@register_tool("entraid", "serviceprincipal")
class EntraidServiceprincipalListTool(AzureTool):
    """Tool for listing Entra ID service principals."""

    @property
    def name(self) -> str:
        return "entraid_serviceprincipal_list"

    @property
    def description(self) -> str:
        return (
            "List service principals (enterprise applications) in Microsoft Entra ID. "
            "Service principals represent applications in your tenant, including "
            "your own apps, Microsoft apps, and third-party apps. "
            "Use filter to narrow by servicePrincipalType or accountEnabled. "
            "Requires Application.Read.All permission."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return EntraidServiceprincipalListOptions

    async def execute(self, options: EntraidServiceprincipalListOptions) -> Any:
        """Execute the list service principals operation."""
        service = EntraIdService()

        try:
            return await service.list_service_principals(
                filter_query=options.filter_query,
                search=options.search,
                detail_level=options.detail_level,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Service Principal") from e


@register_tool("entraid", "serviceprincipal")
class EntraidServiceprincipalGetTool(AzureTool):
    """Tool for getting a specific Entra ID service principal."""

    @property
    def name(self) -> str:
        return "entraid_serviceprincipal_get"

    @property
    def description(self) -> str:
        return (
            "Get a specific service principal (enterprise application) from Microsoft Entra ID. "
            "Returns detailed information including credentials, permissions, and sign-in settings. "
            "Requires Application.Read.All permission."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return EntraidServiceprincipalGetOptions

    async def execute(self, options: EntraidServiceprincipalGetOptions) -> Any:
        """Execute the get service principal operation."""
        service = EntraIdService()

        try:
            return await service.get_service_principal(
                sp_id=options.sp_id,
                detail_level=options.detail_level,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Service Principal") from e
