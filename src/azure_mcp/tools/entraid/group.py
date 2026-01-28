"""Entra ID group tools.

Provides tools for group management in Microsoft Entra ID:
- List groups with filtering and search
- Get group details
- Get group members
- Get group owners
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.entraid.service import EntraIdService


class EntraidGroupListOptions(BaseModel):
    """Options for listing Entra ID groups."""

    filter_query: str = Field(
        default="",
        description=(
            'OData filter expression (e.g., "securityEnabled eq true", '
            '"mailEnabled eq true", "groupTypes/any(c:c eq \'Unified\')"). '
            "Leave empty for all groups."
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
            "'summary' (essential fields: id, displayName, description, mail, securityEnabled), "
            "'full' (all group properties including membership rules, sync status)."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of groups to return (1-999).",
    )


class EntraidGroupGetOptions(BaseModel):
    """Options for getting a specific Entra ID group."""

    group_id: str = Field(
        ...,
        description="Group ID (GUID). Required.",
    )
    detail_level: Literal["summary", "full"] = Field(
        default="summary",
        description=(
            "Level of detail to return: 'summary' (essential fields), 'full' (all properties)."
        ),
    )


class EntraidGroupMembersOptions(BaseModel):
    """Options for getting group members."""

    group_id: str = Field(
        ...,
        description="Group ID (GUID). Required.",
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of members to return.",
    )


class EntraidGroupOwnersOptions(BaseModel):
    """Options for getting group owners."""

    group_id: str = Field(
        ...,
        description="Group ID (GUID). Required.",
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of owners to return.",
    )


@register_tool("entraid", "group")
class EntraidGroupListTool(AzureTool):
    """Tool for listing Entra ID groups."""

    @property
    def name(self) -> str:
        return "entraid_group_list"

    @property
    def description(self) -> str:
        return (
            "List groups in Microsoft Entra ID (Azure AD). "
            "Supports filtering by security enabled, mail enabled, or group type. "
            "Use search for partial name matching. "
            "Returns group identity, type info, and membership rules. "
            "Requires Group.Read.All permission."
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
        return EntraidGroupListOptions

    async def execute(self, options: EntraidGroupListOptions) -> Any:
        """Execute the list groups operation."""
        service = EntraIdService()

        try:
            return await service.list_groups(
                filter_query=options.filter_query,
                search=options.search,
                detail_level=options.detail_level,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Group") from e


@register_tool("entraid", "group")
class EntraidGroupGetTool(AzureTool):
    """Tool for getting a specific Entra ID group."""

    @property
    def name(self) -> str:
        return "entraid_group_get"

    @property
    def description(self) -> str:
        return (
            "Get a specific group from Microsoft Entra ID by ID. "
            "Returns detailed group information including type, membership rules, and sync status. "
            "Use detail_level to control the amount of data returned. "
            "Requires Group.Read.All permission."
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
        return EntraidGroupGetOptions

    async def execute(self, options: EntraidGroupGetOptions) -> Any:
        """Execute the get group operation."""
        service = EntraIdService()

        try:
            return await service.get_group(
                group_id=options.group_id,
                detail_level=options.detail_level,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Group") from e


@register_tool("entraid", "group")
class EntraidGroupMembersTool(AzureTool):
    """Tool for getting group members."""

    @property
    def name(self) -> str:
        return "entraid_group_members"

    @property
    def description(self) -> str:
        return (
            "Get members of a group in Microsoft Entra ID. "
            "Returns a list of members which can include users, groups, service principals, "
            "and other directory objects. "
            "Useful for auditing group membership and access control. "
            "Requires GroupMember.Read.All permission."
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
        return EntraidGroupMembersOptions

    async def execute(self, options: EntraidGroupMembersOptions) -> Any:
        """Execute the get group members operation."""
        service = EntraIdService()

        try:
            return await service.get_group_members(
                group_id=options.group_id,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Group Members") from e


@register_tool("entraid", "group")
class EntraidGroupOwnersTool(AzureTool):
    """Tool for getting group owners."""

    @property
    def name(self) -> str:
        return "entraid_group_owners"

    @property
    def description(self) -> str:
        return (
            "Get owners of a group in Microsoft Entra ID. "
            "Returns a list of users or service principals who own the group. "
            "Owners can manage group membership and settings. "
            "Useful for auditing group governance. "
            "Requires GroupMember.Read.All permission."
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
        return EntraidGroupOwnersOptions

    async def execute(self, options: EntraidGroupOwnersOptions) -> Any:
        """Execute the get group owners operation."""
        service = EntraIdService()

        try:
            return await service.get_group_owners(
                group_id=options.group_id,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Group Owners") from e
