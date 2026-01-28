"""Entra ID user tools.

Provides tools for user management in Microsoft Entra ID:
- List users with filtering and search
- Get user details
- Get user's manager
- Get user's direct reports
- Get user's group/role memberships
- Get user's license details
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.entraid.service import EntraIdService


class EntraidUserListOptions(BaseModel):
    """Options for listing Entra ID users."""

    filter_query: str = Field(
        default="",
        description=(
            "OData filter expression (e.g., \"department eq 'Engineering'\", "
            '"accountEnabled eq true"). Leave empty for all users.'
        ),
    )
    search: str = Field(
        default="",
        description=(
            "Search by displayName or mail. Partial matching supported. "
            "Leave empty for no search filter."
        ),
    )
    detail_level: Literal["summary", "full", "security"] = Field(
        default="summary",
        description=(
            "Level of detail to return: "
            "'summary' (essential fields: id, displayName, mail, jobTitle, department, accountEnabled), "
            "'full' (all user properties including contact, location, employment), "
            "'security' (security-focused: signInActivity, passwordInfo, syncStatus)."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of users to return (1-999).",
    )


class EntraidUserGetOptions(BaseModel):
    """Options for getting a specific Entra ID user."""

    user_id: str = Field(
        ...,
        description=("User ID (GUID) or userPrincipalName (e.g., 'user@contoso.com'). Required."),
    )
    detail_level: Literal["summary", "full", "security"] = Field(
        default="summary",
        description=(
            "Level of detail to return: "
            "'summary' (essential fields), "
            "'full' (all properties), "
            "'security' (security-focused)."
        ),
    )


class EntraidUserManagerOptions(BaseModel):
    """Options for getting a user's manager."""

    user_id: str = Field(
        ...,
        description=("User ID (GUID) or userPrincipalName (e.g., 'user@contoso.com'). Required."),
    )


class EntraidUserDirectreportsOptions(BaseModel):
    """Options for getting a user's direct reports."""

    user_id: str = Field(
        ...,
        description=("User ID (GUID) or userPrincipalName of the manager. Required."),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of direct reports to return.",
    )


class EntraidUserMemberofOptions(BaseModel):
    """Options for getting a user's group and role memberships."""

    user_id: str = Field(
        ...,
        description=("User ID (GUID) or userPrincipalName (e.g., 'user@contoso.com'). Required."),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of memberships to return.",
    )


class EntraidUserLicensesOptions(BaseModel):
    """Options for getting a user's license details."""

    user_id: str = Field(
        ...,
        description=("User ID (GUID) or userPrincipalName (e.g., 'user@contoso.com'). Required."),
    )


@register_tool("entraid", "user")
class EntraidUserListTool(AzureTool):
    """Tool for listing Entra ID users."""

    @property
    def name(self) -> str:
        return "entraid_user_list"

    @property
    def description(self) -> str:
        return (
            "List users in Microsoft Entra ID (Azure AD). "
            "Supports filtering by department, job title, account status, or any OData-supported property. "
            "Use search for partial name/email matching. "
            "Returns user identity, organization info, and account status. "
            "Requires User.Read.All permission."
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
        return EntraidUserListOptions

    async def execute(self, options: EntraidUserListOptions) -> Any:
        """Execute the list users operation."""
        service = EntraIdService()

        try:
            return await service.list_users(
                filter_query=options.filter_query,
                search=options.search,
                detail_level=options.detail_level,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID User") from e


@register_tool("entraid", "user")
class EntraidUserGetTool(AzureTool):
    """Tool for getting a specific Entra ID user."""

    @property
    def name(self) -> str:
        return "entraid_user_get"

    @property
    def description(self) -> str:
        return (
            "Get a specific user from Microsoft Entra ID by ID or UPN. "
            "Returns detailed user information including identity, organization, contact, and security info. "
            "Use detail_level to control the amount of data returned. "
            "Requires User.Read.All permission."
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
        return EntraidUserGetOptions

    async def execute(self, options: EntraidUserGetOptions) -> Any:
        """Execute the get user operation."""
        service = EntraIdService()

        try:
            return await service.get_user(
                user_id=options.user_id,
                detail_level=options.detail_level,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID User") from e


@register_tool("entraid", "user")
class EntraidUserManagerTool(AzureTool):
    """Tool for getting a user's manager."""

    @property
    def name(self) -> str:
        return "entraid_user_manager"

    @property
    def description(self) -> str:
        return (
            "Get the manager of a specific user in Microsoft Entra ID. "
            "Returns the manager's user information, or empty if no manager is assigned. "
            "Useful for understanding org hierarchy. "
            "Requires User.Read.All permission."
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
        return EntraidUserManagerOptions

    async def execute(self, options: EntraidUserManagerOptions) -> Any:
        """Execute the get manager operation."""
        service = EntraIdService()

        try:
            return await service.get_user_manager(user_id=options.user_id)
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID User Manager") from e


@register_tool("entraid", "user")
class EntraidUserDirectreportsTool(AzureTool):
    """Tool for getting a user's direct reports."""

    @property
    def name(self) -> str:
        return "entraid_user_directreports"

    @property
    def description(self) -> str:
        return (
            "Get users who report directly to a specified user in Microsoft Entra ID. "
            "Returns a list of direct report users with their basic information. "
            "Useful for understanding org hierarchy and team structure. "
            "Requires User.Read.All permission."
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
        return EntraidUserDirectreportsOptions

    async def execute(self, options: EntraidUserDirectreportsOptions) -> Any:
        """Execute the get direct reports operation."""
        service = EntraIdService()

        try:
            return await service.get_user_direct_reports(
                user_id=options.user_id,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID User Direct Reports") from e


@register_tool("entraid", "user")
class EntraidUserMemberofTool(AzureTool):
    """Tool for getting a user's group and role memberships."""

    @property
    def name(self) -> str:
        return "entraid_user_memberof"

    @property
    def description(self) -> str:
        return (
            "Get groups and directory roles that a user is a member of in Microsoft Entra ID. "
            "Returns a list of groups (security groups, Microsoft 365 groups) and directory roles. "
            "Useful for understanding user permissions and group memberships. "
            "Requires User.Read.All and GroupMember.Read.All permissions."
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
        return EntraidUserMemberofOptions

    async def execute(self, options: EntraidUserMemberofOptions) -> Any:
        """Execute the get member of operation."""
        service = EntraIdService()

        try:
            return await service.get_user_member_of(
                user_id=options.user_id,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID User Memberships") from e


@register_tool("entraid", "user")
class EntraidUserLicensesTool(AzureTool):
    """Tool for getting a user's license details."""

    @property
    def name(self) -> str:
        return "entraid_user_licenses"

    @property
    def description(self) -> str:
        return (
            "Get license details for a user in Microsoft Entra ID. "
            "Returns assigned licenses including SKU info and enabled service plans. "
            "Useful for license management and compliance checking. "
            "Requires User.Read.All permission."
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
        return EntraidUserLicensesOptions

    async def execute(self, options: EntraidUserLicensesOptions) -> Any:
        """Execute the get licenses operation."""
        service = EntraIdService()

        try:
            return await service.get_user_licenses(user_id=options.user_id)
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID User Licenses") from e
