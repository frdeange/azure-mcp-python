"""RBAC role assignment tools.

Tools for managing Azure RBAC role assignments.
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
# RBAC ASSIGNMENT LIST
# =============================================================================


class RbacAssignmentListOptions(BaseModel):
    """Options for listing RBAC role assignments."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name.",
    )
    scope: str = Field(
        default="",
        description=(
            "Scope to list assignments at. "
            "Can be a subscription, resource group, or resource ID. "
            "Leave empty for subscription level."
        ),
    )
    principal_id: str = Field(
        default="",
        description="Filter by principal ID (user, group, or service principal object ID).",
    )


@register_tool("rbac", "assignments")
class RbacAssignmentListTool(AzureTool):
    """Tool to list Azure RBAC role assignments."""

    @property
    def name(self) -> str:
        return "rbac_assignment_list"

    @property
    def description(self) -> str:
        return (
            "List Azure RBAC role assignments at a scope. "
            "Shows who has what role on a resource, resource group, or subscription. "
            "Use this to audit permissions or check existing assignments before creating new ones."
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
        return RbacAssignmentListOptions

    async def execute(self, options: RbacAssignmentListOptions) -> Any:
        service = RbacService()
        try:
            return await service.list_role_assignments(
                subscription=options.subscription,
                scope=options.scope,
                principal_id=options.principal_id,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Role Assignments")


# =============================================================================
# RBAC ASSIGNMENT CREATE
# =============================================================================


class RbacAssignmentCreateOptions(BaseModel):
    """Options for creating a RBAC role assignment."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name.",
    )
    scope: str = Field(
        ...,
        description=(
            "The scope for the assignment. Examples: "
            "'/subscriptions/{sub-id}' for subscription, "
            "'/subscriptions/{sub-id}/resourceGroups/{rg}' for resource group, "
            "'/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{name}' for resource."
        ),
    )
    role_name: str = Field(
        ...,
        description=(
            "Display name of the role to assign (e.g., 'Storage Blob Data Contributor'). "
            "Only roles in the allowed whitelist can be assigned. "
            "Use rbac_allowed_list to see allowed roles."
        ),
    )
    principal_id: str = Field(
        ...,
        description="Object ID of the principal (user, group, or service principal) to assign the role to.",
    )
    principal_type: str = Field(
        default="ServicePrincipal",
        description="Type of principal: 'User', 'Group', or 'ServicePrincipal'. Default is ServicePrincipal.",
    )


@register_tool("rbac", "assignments")
class RbacAssignmentCreateTool(AzureTool):
    """Tool to create an Azure RBAC role assignment."""

    @property
    def name(self) -> str:
        return "rbac_assignment_create"

    @property
    def description(self) -> str:
        return (
            "Create an Azure RBAC role assignment to grant permissions to a user, group, or service principal. "
            "SECURITY: Only roles in the allowed whitelist can be assigned. "
            "Dangerous roles like Owner and Contributor are blocked. "
            "Use rbac_allowed_list to see which roles can be assigned."
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
        return RbacAssignmentCreateOptions

    async def execute(self, options: RbacAssignmentCreateOptions) -> Any:
        service = RbacService()
        try:
            return await service.create_role_assignment(
                subscription=options.subscription,
                scope=options.scope,
                role_name=options.role_name,
                principal_id=options.principal_id,
                principal_type=options.principal_type,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Role Assignment")


# =============================================================================
# RBAC ASSIGNMENT DELETE
# =============================================================================


class RbacAssignmentDeleteOptions(BaseModel):
    """Options for deleting a RBAC role assignment."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name.",
    )
    scope: str = Field(
        ...,
        description="The scope of the assignment to delete.",
    )
    assignment_name: str = Field(
        ...,
        description="The name (GUID) of the role assignment to delete. Get this from rbac_assignment_list.",
    )


@register_tool("rbac", "assignments")
class RbacAssignmentDeleteTool(AzureTool):
    """Tool to delete an Azure RBAC role assignment."""

    @property
    def name(self) -> str:
        return "rbac_assignment_delete"

    @property
    def description(self) -> str:
        return (
            "Delete an Azure RBAC role assignment to revoke permissions. "
            "Use rbac_assignment_list to find the assignment name (GUID) to delete."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return RbacAssignmentDeleteOptions

    async def execute(self, options: RbacAssignmentDeleteOptions) -> Any:
        service = RbacService()
        try:
            return await service.delete_role_assignment(
                subscription=options.subscription,
                scope=options.scope,
                assignment_name=options.assignment_name,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Role Assignment")
