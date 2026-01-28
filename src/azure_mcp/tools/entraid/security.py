"""Entra ID security and audit tools.

Provides tools for security and audit in Microsoft Entra ID:
- List directory roles
- List role assignments
- List sign-in logs (requires P1/P2 license)
- List audit logs (requires P1/P2 license)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.entraid.service import EntraIdService


class EntraidDirectoryRolesOptions(BaseModel):
    """Options for listing Entra ID directory roles."""

    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of roles to return.",
    )


class EntraidRoleAssignmentsOptions(BaseModel):
    """Options for listing Entra ID role assignments."""

    principal_id: str = Field(
        default="",
        description=(
            "Filter by principal ID (user, group, or service principal GUID). "
            "Leave empty for all assignments."
        ),
    )
    role_definition_id: str = Field(
        default="",
        description=("Filter by role definition ID (GUID). Leave empty for all roles."),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of assignments to return.",
    )


class EntraidSigninLogsOptions(BaseModel):
    """Options for listing Entra ID sign-in logs.

    NOTE: This operation requires an Entra ID P1 or P2 license.
    """

    user_id: str = Field(
        default="",
        description=("Filter by user ID (GUID). Leave empty for all users."),
    )
    app_id: str = Field(
        default="",
        description=("Filter by application ID (client ID). Leave empty for all applications."),
    )
    filter_query: str = Field(
        default="",
        description=(
            'Additional OData filter expression (e.g., "status/errorCode eq 0" for successful sign-ins, '
            '"createdDateTime ge 2024-01-01T00:00:00Z"). '
            "Leave empty for no additional filter."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of sign-in logs to return.",
    )


class EntraidAuditLogsOptions(BaseModel):
    """Options for listing Entra ID audit logs.

    NOTE: This operation requires an Entra ID P1 or P2 license.
    """

    category: str = Field(
        default="",
        description=(
            "Filter by activity category (e.g., 'UserManagement', 'GroupManagement', "
            "'ApplicationManagement', 'RoleManagement', 'DirectoryManagement'). "
            "Leave empty for all categories."
        ),
    )
    initiated_by: str = Field(
        default="",
        description=(
            "Filter by the user ID who initiated the action. Leave empty for all initiators."
        ),
    )
    target_resource: str = Field(
        default="",
        description=("Filter by target resource ID. Leave empty for all targets."),
    )
    filter_query: str = Field(
        default="",
        description=(
            'Additional OData filter expression (e.g., "activityDateTime ge 2024-01-01T00:00:00Z"). '
            "Leave empty for no additional filter."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=999,
        description="Maximum number of audit logs to return.",
    )


@register_tool("entraid", "security")
class EntraidDirectoryRolesTool(AzureTool):
    """Tool for listing Entra ID directory roles."""

    @property
    def name(self) -> str:
        return "entraid_directory_roles"

    @property
    def description(self) -> str:
        return (
            "List activated directory roles in Microsoft Entra ID. "
            "Returns built-in roles like Global Administrator, User Administrator, etc. "
            "Only shows roles that have been activated (have at least one member). "
            "Requires RoleManagement.Read.Directory permission."
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
        return EntraidDirectoryRolesOptions

    async def execute(self, options: EntraidDirectoryRolesOptions) -> Any:
        """Execute the list directory roles operation."""
        service = EntraIdService()

        try:
            return await service.list_directory_roles(top=options.top)
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Directory Roles") from e


@register_tool("entraid", "security")
class EntraidRoleAssignmentsTool(AzureTool):
    """Tool for listing Entra ID role assignments."""

    @property
    def name(self) -> str:
        return "entraid_role_assignments"

    @property
    def description(self) -> str:
        return (
            "List role assignments in Microsoft Entra ID. "
            "Shows which users, groups, or service principals have been assigned directory roles. "
            "Can filter by principal ID or role definition ID. "
            "Useful for security audits and access reviews. "
            "Requires RoleManagement.Read.Directory permission."
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
        return EntraidRoleAssignmentsOptions

    async def execute(self, options: EntraidRoleAssignmentsOptions) -> Any:
        """Execute the list role assignments operation."""
        service = EntraIdService()

        try:
            return await service.list_role_assignments(
                principal_id=options.principal_id,
                role_definition_id=options.role_definition_id,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Role Assignments") from e


@register_tool("entraid", "security")
class EntraidSigninLogsTool(AzureTool):
    """Tool for listing Entra ID sign-in logs.

    NOTE: This operation requires an Entra ID P1 or P2 license.
    """

    @property
    def name(self) -> str:
        return "entraid_signin_logs"

    @property
    def description(self) -> str:
        return (
            "List sign-in logs from Microsoft Entra ID. "
            "Shows user sign-in activity including success/failure, location, device, and app info. "
            "Useful for security monitoring and investigating suspicious activity. "
            "⚠️ REQUIRES ENTRA ID P1 OR P2 LICENSE. "
            "Requires AuditLog.Read.All permission. "
            "See: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins"
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
        return EntraidSigninLogsOptions

    async def execute(self, options: EntraidSigninLogsOptions) -> Any:
        """Execute the list sign-in logs operation."""
        service = EntraIdService()

        try:
            return await service.list_signin_logs(
                user_id=options.user_id,
                app_id=options.app_id,
                filter_query=options.filter_query,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Sign-in Logs") from e


@register_tool("entraid", "security")
class EntraidAuditLogsTool(AzureTool):
    """Tool for listing Entra ID audit logs.

    NOTE: This operation requires an Entra ID P1 or P2 license.
    """

    @property
    def name(self) -> str:
        return "entraid_audit_logs"

    @property
    def description(self) -> str:
        return (
            "List directory audit logs from Microsoft Entra ID. "
            "Shows changes to directory objects like users, groups, apps, and roles. "
            "Useful for compliance, security audits, and tracking administrative changes. "
            "⚠️ REQUIRES ENTRA ID P1 OR P2 LICENSE. "
            "Requires AuditLog.Read.All permission. "
            "See: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-audit-logs"
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
        return EntraidAuditLogsOptions

    async def execute(self, options: EntraidAuditLogsOptions) -> Any:
        """Execute the list audit logs operation."""
        service = EntraIdService()

        try:
            return await service.list_audit_logs(
                category=options.category,
                initiated_by=options.initiated_by,
                target_resource=options.target_resource,
                filter_query=options.filter_query,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Entra ID Audit Logs") from e
