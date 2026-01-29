"""Microsoft Graph app role tools.

Tools for managing Microsoft Graph application permissions (app roles).
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
# RBAC APPROLE LIST
# =============================================================================


class RbacApproleListOptions(BaseModel):
    """Options for listing app role assignments."""

    principal_id: str = Field(
        ...,
        description=(
            "Object ID of the service principal (managed identity) to list app roles for. "
            "This is the 'id' field from Azure AD, not the application/client ID."
        ),
    )


@register_tool("rbac", "approles")
class RbacApproleListTool(AzureTool):
    """Tool to list Microsoft Graph app role assignments for a principal."""

    @property
    def name(self) -> str:
        return "rbac_approle_list"

    @property
    def description(self) -> str:
        return (
            "List Microsoft Graph app role assignments (application permissions) for a service principal. "
            "Shows what Graph API permissions have been granted to a managed identity or app registration. "
            "Use this to audit permissions or check what a service principal can access."
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
        return RbacApproleListOptions

    async def execute(self, options: RbacApproleListOptions) -> Any:
        service = RbacService()
        try:
            return await service.list_app_role_assignments(
                principal_id=options.principal_id,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="App Role Assignments")


# =============================================================================
# RBAC APPROLE GRANT
# =============================================================================


class RbacApproleGrantOptions(BaseModel):
    """Options for granting an app role."""

    principal_id: str = Field(
        ...,
        description=(
            "Object ID of the service principal (managed identity) to grant the permission to. "
            "This is the 'id' field from Azure AD, not the application/client ID."
        ),
    )
    permission_name: str = Field(
        ...,
        description=(
            "Name of the Microsoft Graph permission to grant (e.g., 'User.Read.All'). "
            "Only permissions in the allowed whitelist can be granted. "
            "Use rbac_allowed_list to see allowed permissions."
        ),
    )


@register_tool("rbac", "approles")
class RbacApproleGrantTool(AzureTool):
    """Tool to grant a Microsoft Graph app role to a principal."""

    @property
    def name(self) -> str:
        return "rbac_approle_grant"

    @property
    def description(self) -> str:
        return (
            "Grant a Microsoft Graph application permission (app role) to a service principal. "
            "SECURITY: Only permissions in the allowed whitelist can be granted. "
            "This grants tenant-wide access to the specified API. "
            "Use rbac_allowed_list to see which permissions can be granted."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=False,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return RbacApproleGrantOptions

    async def execute(self, options: RbacApproleGrantOptions) -> Any:
        service = RbacService()
        try:
            return await service.grant_app_role(
                principal_id=options.principal_id,
                permission_name=options.permission_name,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="App Role Grant")
