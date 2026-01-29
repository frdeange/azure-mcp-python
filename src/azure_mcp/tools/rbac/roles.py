"""RBAC role definition tools.

Tools for listing and querying Azure RBAC role definitions.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.rbac.service import RbacService


# =============================================================================
# RBAC ROLE LIST
# =============================================================================


class RbacRoleListOptions(BaseModel):
    """Options for listing RBAC role definitions."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name.",
    )
    scope: str = Field(
        default="",
        description="Scope to list roles at. Leave empty for subscription level.",
    )
    filter_builtin: bool = Field(
        default=True,
        description="If true, only return built-in roles. If false, include custom roles.",
    )


@register_tool("rbac", "roles")
class RbacRoleListTool(AzureTool):
    """Tool to list Azure RBAC role definitions."""

    @property
    def name(self) -> str:
        return "rbac_role_list"

    @property
    def description(self) -> str:
        return (
            "List Azure RBAC role definitions available at a scope. "
            "Shows role names, descriptions, and whether they are allowed for assignment. "
            "Use this to discover available roles before creating assignments."
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
        return RbacRoleListOptions

    async def execute(self, options: RbacRoleListOptions) -> Any:
        service = RbacService()
        try:
            return await service.list_role_definitions(
                subscription=options.subscription,
                scope=options.scope,
                filter_builtin=options.filter_builtin,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Role Definitions")


# =============================================================================
# RBAC ROLE GET
# =============================================================================


class RbacRoleGetOptions(BaseModel):
    """Options for getting a specific RBAC role definition."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name.",
    )
    role_name: str = Field(
        ...,
        description="Display name of the role (e.g., 'Storage Blob Data Reader').",
    )


@register_tool("rbac", "roles")
class RbacRoleGetTool(AzureTool):
    """Tool to get details of a specific RBAC role."""

    @property
    def name(self) -> str:
        return "rbac_role_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about a specific Azure RBAC role by name. "
            "Returns permissions, actions, data actions, and whether the role is allowed for assignment."
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
        return RbacRoleGetOptions

    async def execute(self, options: RbacRoleGetOptions) -> Any:
        service = RbacService()
        try:
            return await service.get_role_definition(
                subscription=options.subscription,
                role_name=options.role_name,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Role Definition")


# =============================================================================
# RBAC ALLOWED LIST
# =============================================================================


class RbacAllowedListOptions(BaseModel):
    """Options for listing allowed roles and permissions."""

    pass  # No options needed


@register_tool("rbac", "roles")
class RbacAllowedListTool(AzureTool):
    """Tool to list allowed roles and permissions for assignment."""

    @property
    def name(self) -> str:
        return "rbac_allowed_list"

    @property
    def description(self) -> str:
        return (
            "List the whitelist of allowed Azure RBAC roles and Microsoft Graph permissions "
            "that can be assigned using this MCP server. Also shows blocked roles. "
            "Use this to understand what permissions can be granted."
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
        return RbacAllowedListOptions

    async def execute(self, options: RbacAllowedListOptions) -> Any:
        service = RbacService()
        try:
            return await service.get_allowed_roles()
        except Exception as e:
            raise handle_azure_error(e, resource="Allowed Roles")
