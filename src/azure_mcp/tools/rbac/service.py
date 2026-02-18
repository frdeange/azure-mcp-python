"""RBAC service for Azure role and permission management.

Provides methods for managing Azure RBAC role assignments and Microsoft Graph app roles.
Includes security whitelists to prevent privilege escalation.
"""

from __future__ import annotations

import uuid
import structlog
from typing import Any

from azure_mcp.core.base import AzureService

logger = structlog.get_logger()

# =============================================================================
# SECURITY WHITELISTS
# =============================================================================

# Allowed Azure RBAC roles for assignment (by display name)
# These are data plane roles that don't grant management plane access
ALLOWED_RBAC_ROLES: set[str] = {
    # Storage - Data Plane
    "Storage Blob Data Reader",
    "Storage Blob Data Contributor",
    "Storage Blob Data Owner",
    "Storage Queue Data Reader",
    "Storage Queue Data Contributor",
    "Storage Queue Data Message Processor",
    "Storage Queue Data Message Sender",
    "Storage Table Data Reader",
    "Storage Table Data Contributor",
    "Storage File Data SMB Share Reader",
    "Storage File Data SMB Share Contributor",
    # Cosmos DB - Data Plane
    "Cosmos DB Account Reader Role",
    "Cosmos DB Built-in Data Reader",
    "Cosmos DB Built-in Data Contributor",
    "DocumentDB Account Contributor",
    # Key Vault - Data Plane
    "Key Vault Reader",
    "Key Vault Secrets User",
    "Key Vault Secrets Officer",
    "Key Vault Crypto User",
    "Key Vault Crypto Officer",
    "Key Vault Certificates Officer",
    # Azure AI Search - Data Plane
    "Search Index Data Reader",
    "Search Index Data Contributor",
    "Search Service Contributor",
    # Cost Management
    "Cost Management Reader",
    "Cost Management Contributor",
    # Monitor
    "Monitoring Reader",
    "Monitoring Contributor",
    "Log Analytics Reader",
    "Log Analytics Contributor",
    # General Read-only
    "Reader",
}

# Explicitly blocked roles (dangerous - can escalate privileges)
BLOCKED_RBAC_ROLES: set[str] = {
    "Owner",
    "Contributor",
    "User Access Administrator",
    "Role Based Access Control Administrator",
}

# Allowed Microsoft Graph app roles (by permission name)
ALLOWED_GRAPH_PERMISSIONS: set[str] = {
    # Users - Read only
    "User.Read.All",
    "User.ReadBasic.All",
    # Groups - Read only
    "Group.Read.All",
    "GroupMember.Read.All",
    # Applications - Read only
    "Application.Read.All",
    # Directory - Read only
    "Directory.Read.All",
    # Service Principals - Read only
    "ServicePrincipalEndpoint.Read.All",
    # Role Management - Read only (for entraid_directory_roles, entraid_role_assignments)
    "RoleManagement.Read.Directory",
    # Audit Logs - Read only (for entraid_signin_logs, entraid_audit_logs; requires P1/P2)
    "AuditLog.Read.All",
}

# Microsoft Graph service principal appId (constant)
MICROSOFT_GRAPH_APP_ID = "00000003-0000-0000-c000-000000000000"


class RbacService(AzureService):
    """Service for Azure RBAC and Microsoft Graph permission operations."""

    # =========================================================================
    # AZURE RBAC - ROLE DEFINITIONS
    # =========================================================================

    async def list_role_definitions(
        self,
        subscription: str,
        scope: str = "",
        filter_builtin: bool = True,
    ) -> list[dict[str, Any]]:
        """
        List role definitions available at a scope.

        Args:
            subscription: Subscription ID or name.
            scope: Optional scope (defaults to subscription level).
            filter_builtin: If True, only return built-in roles.

        Returns:
            List of role definitions.
        """
        from azure.mgmt.authorization import AuthorizationManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        if not scope:
            scope = f"/subscriptions/{sub_id}"

        client = AuthorizationManagementClient(credential, sub_id)

        # Build filter
        odata_filter = None
        if filter_builtin:
            odata_filter = "type eq 'BuiltInRole'"

        roles = []
        for role in client.role_definitions.list(scope, filter=odata_filter):
            roles.append(
                {
                    "id": role.id,
                    "name": role.name,
                    "role_name": role.role_name,
                    "description": role.description,
                    "role_type": role.role_type,
                    "permissions": [
                        {
                            "actions": list(p.actions) if p.actions else [],
                            "not_actions": list(p.not_actions) if p.not_actions else [],
                            "data_actions": list(p.data_actions) if p.data_actions else [],
                            "not_data_actions": list(p.not_data_actions)
                            if p.not_data_actions
                            else [],
                        }
                        for p in (role.permissions or [])
                    ],
                    "assignable_scopes": list(role.assignable_scopes)
                    if role.assignable_scopes
                    else [],
                    "is_allowed": role.role_name in ALLOWED_RBAC_ROLES,
                    "is_blocked": role.role_name in BLOCKED_RBAC_ROLES,
                }
            )

        return roles

    async def get_role_definition(
        self,
        subscription: str,
        role_name: str,
    ) -> dict[str, Any]:
        """
        Get a role definition by name.

        Args:
            subscription: Subscription ID or name.
            role_name: Display name of the role (e.g., "Storage Blob Data Reader").

        Returns:
            Role definition details.
        """
        from azure.mgmt.authorization import AuthorizationManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        scope = f"/subscriptions/{sub_id}"
        client = AuthorizationManagementClient(credential, sub_id)

        # Filter by role name
        odata_filter = f"roleName eq '{role_name}'"

        for role in client.role_definitions.list(scope, filter=odata_filter):
            return {
                "id": role.id,
                "name": role.name,
                "role_name": role.role_name,
                "description": role.description,
                "role_type": role.role_type,
                "permissions": [
                    {
                        "actions": list(p.actions) if p.actions else [],
                        "not_actions": list(p.not_actions) if p.not_actions else [],
                        "data_actions": list(p.data_actions) if p.data_actions else [],
                        "not_data_actions": list(p.not_data_actions) if p.not_data_actions else [],
                    }
                    for p in (role.permissions or [])
                ],
                "assignable_scopes": list(role.assignable_scopes) if role.assignable_scopes else [],
                "is_allowed": role.role_name in ALLOWED_RBAC_ROLES,
                "is_blocked": role.role_name in BLOCKED_RBAC_ROLES,
            }

        raise ValueError(f"Role '{role_name}' not found")

    # =========================================================================
    # AZURE RBAC - ROLE ASSIGNMENTS
    # =========================================================================

    async def list_role_assignments(
        self,
        subscription: str,
        scope: str = "",
        principal_id: str = "",
    ) -> list[dict[str, Any]]:
        """
        List role assignments at a scope.

        Args:
            subscription: Subscription ID or name.
            scope: Optional scope to filter (defaults to subscription).
            principal_id: Optional principal ID to filter.

        Returns:
            List of role assignments.
        """
        from azure.mgmt.authorization import AuthorizationManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        if not scope:
            scope = f"/subscriptions/{sub_id}"

        client = AuthorizationManagementClient(credential, sub_id)

        # Build filter
        odata_filter = None
        if principal_id:
            odata_filter = f"principalId eq '{principal_id}'"

        assignments = []
        for assignment in client.role_assignments.list_for_scope(scope, filter=odata_filter):
            # Get role name from definition ID
            role_name = "Unknown"
            if assignment.role_definition_id:
                try:
                    role_def = client.role_definitions.get_by_id(assignment.role_definition_id)
                    role_name = role_def.role_name
                except Exception:
                    pass

            assignments.append(
                {
                    "id": assignment.id,
                    "name": assignment.name,
                    "principal_id": assignment.principal_id,
                    "principal_type": assignment.principal_type,
                    "role_definition_id": assignment.role_definition_id,
                    "role_name": role_name,
                    "scope": assignment.scope,
                    "created_on": assignment.created_on.isoformat()
                    if assignment.created_on
                    else None,
                    "updated_on": assignment.updated_on.isoformat()
                    if assignment.updated_on
                    else None,
                    "created_by": assignment.created_by,
                }
            )

        return assignments

    async def create_role_assignment(
        self,
        subscription: str,
        scope: str,
        role_name: str,
        principal_id: str,
        principal_type: str = "ServicePrincipal",
    ) -> dict[str, Any]:
        """
        Create a role assignment.

        Args:
            subscription: Subscription ID or name.
            scope: The scope for the assignment (resource, RG, or subscription).
            role_name: Display name of the role to assign.
            principal_id: Object ID of the principal (user, group, or service principal).
            principal_type: Type of principal (User, Group, ServicePrincipal).

        Returns:
            Created role assignment.

        Raises:
            ValueError: If role is not in the allowed whitelist.
        """
        from azure.mgmt.authorization import AuthorizationManagementClient
        from azure.mgmt.authorization.models import RoleAssignmentCreateParameters

        # Security check: verify role is allowed
        if role_name in BLOCKED_RBAC_ROLES:
            logger.warning(
                "Blocked role assignment attempt",
                role_name=role_name,
                principal_id=principal_id,
                scope=scope,
            )
            raise ValueError(
                f"Role '{role_name}' is blocked for security reasons. "
                f"Blocked roles: {', '.join(sorted(BLOCKED_RBAC_ROLES))}"
            )

        if role_name not in ALLOWED_RBAC_ROLES:
            logger.warning(
                "Unauthorized role assignment attempt",
                role_name=role_name,
                principal_id=principal_id,
                scope=scope,
            )
            raise ValueError(
                f"Role '{role_name}' is not in the allowed whitelist. "
                f"Allowed roles include: {', '.join(sorted(list(ALLOWED_RBAC_ROLES)[:10]))}..."
            )

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        client = AuthorizationManagementClient(credential, sub_id)

        # Get role definition ID
        role_def = await self.get_role_definition(subscription, role_name)
        role_definition_id = role_def["id"]

        # Generate unique assignment name
        assignment_name = str(uuid.uuid4())

        # Create parameters
        parameters = RoleAssignmentCreateParameters(
            role_definition_id=role_definition_id,
            principal_id=principal_id,
            principal_type=principal_type,
        )

        # Create assignment
        result = client.role_assignments.create(scope, assignment_name, parameters)

        logger.info(
            "Role assignment created",
            role_name=role_name,
            principal_id=principal_id,
            scope=scope,
            assignment_id=result.id,
        )

        return {
            "id": result.id,
            "name": result.name,
            "principal_id": result.principal_id,
            "principal_type": result.principal_type,
            "role_definition_id": result.role_definition_id,
            "role_name": role_name,
            "scope": result.scope,
            "created_on": result.created_on.isoformat() if result.created_on else None,
        }

    async def delete_role_assignment(
        self,
        subscription: str,
        scope: str,
        assignment_name: str,
    ) -> dict[str, Any]:
        """
        Delete a role assignment.

        Args:
            subscription: Subscription ID or name.
            scope: The scope of the assignment.
            assignment_name: The name (GUID) of the assignment to delete.

        Returns:
            Deleted assignment info.
        """
        from azure.mgmt.authorization import AuthorizationManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        client = AuthorizationManagementClient(credential, sub_id)

        result = client.role_assignments.delete(scope, assignment_name)

        logger.info(
            "Role assignment deleted",
            assignment_name=assignment_name,
            scope=scope,
        )

        return {
            "id": result.id,
            "name": result.name,
            "deleted": True,
        }

    # =========================================================================
    # MICROSOFT GRAPH - APP ROLE ASSIGNMENTS
    # =========================================================================

    async def list_app_role_assignments(
        self,
        principal_id: str,
    ) -> list[dict[str, Any]]:
        """
        List app role assignments for a service principal.

        Args:
            principal_id: Object ID of the service principal.

        Returns:
            List of app role assignments.
        """
        from msgraph import GraphServiceClient

        credential = self.get_credential()
        client = GraphServiceClient(credentials=credential)

        result = await client.service_principals.by_service_principal_id(
            principal_id
        ).app_role_assignments.get()

        assignments = []
        for assignment in result.value or []:
            assignments.append(
                {
                    "id": assignment.id,
                    "app_role_id": str(assignment.app_role_id) if assignment.app_role_id else None,
                    "principal_id": str(assignment.principal_id)
                    if assignment.principal_id
                    else None,
                    "principal_display_name": assignment.principal_display_name,
                    "resource_id": str(assignment.resource_id) if assignment.resource_id else None,
                    "resource_display_name": assignment.resource_display_name,
                    "created_date_time": assignment.created_date_time.isoformat()
                    if assignment.created_date_time
                    else None,
                }
            )

        return assignments

    async def grant_app_role(
        self,
        principal_id: str,
        permission_name: str,
        resource_app_id: str = MICROSOFT_GRAPH_APP_ID,
    ) -> dict[str, Any]:
        """
        Grant an app role (application permission) to a service principal.

        Args:
            principal_id: Object ID of the service principal to grant permission to.
            permission_name: Name of the permission (e.g., "User.Read.All").
            resource_app_id: App ID of the resource (defaults to Microsoft Graph).

        Returns:
            Created app role assignment.

        Raises:
            ValueError: If permission is not in the allowed whitelist.
        """
        from msgraph import GraphServiceClient
        from msgraph.generated.models.app_role_assignment import AppRoleAssignment

        # Security check for Graph permissions
        if resource_app_id == MICROSOFT_GRAPH_APP_ID:
            if permission_name not in ALLOWED_GRAPH_PERMISSIONS:
                logger.warning(
                    "Unauthorized Graph permission grant attempt",
                    permission_name=permission_name,
                    principal_id=principal_id,
                )
                raise ValueError(
                    f"Permission '{permission_name}' is not in the allowed whitelist. "
                    f"Allowed permissions: {', '.join(sorted(ALLOWED_GRAPH_PERMISSIONS))}"
                )

        credential = self.get_credential()
        client = GraphServiceClient(credentials=credential)

        # Get the resource service principal
        from msgraph.generated.service_principals.service_principals_request_builder import (
            ServicePrincipalsRequestBuilder,
        )
        from kiota_abstractions.base_request_configuration import RequestConfiguration

        query_params = (
            ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
                filter=f"appId eq '{resource_app_id}'"
            )
        )
        config = RequestConfiguration(query_parameters=query_params)
        resource_sp_result = await client.service_principals.get(request_configuration=config)

        if not resource_sp_result.value:
            raise ValueError(f"Resource service principal with appId '{resource_app_id}' not found")

        resource_sp = resource_sp_result.value[0]
        resource_sp_id = resource_sp.id

        # Find the app role ID
        app_role_id = None
        for app_role in resource_sp.app_roles or []:
            if app_role.value == permission_name:
                app_role_id = app_role.id
                break

        if not app_role_id:
            raise ValueError(f"Permission '{permission_name}' not found in resource")

        # Create the assignment
        assignment = AppRoleAssignment(
            principal_id=uuid.UUID(principal_id),
            resource_id=uuid.UUID(resource_sp_id),
            app_role_id=uuid.UUID(str(app_role_id)),
        )

        result = await client.service_principals.by_service_principal_id(
            resource_sp_id
        ).app_role_assigned_to.post(assignment)

        logger.info(
            "App role granted",
            permission_name=permission_name,
            principal_id=principal_id,
            resource_app_id=resource_app_id,
        )

        return {
            "id": result.id,
            "app_role_id": str(result.app_role_id) if result.app_role_id else None,
            "permission_name": permission_name,
            "principal_id": str(result.principal_id) if result.principal_id else None,
            "resource_id": str(result.resource_id) if result.resource_id else None,
            "resource_display_name": result.resource_display_name,
            "created_date_time": result.created_date_time.isoformat()
            if result.created_date_time
            else None,
        }

    async def get_allowed_roles(self) -> dict[str, Any]:
        """
        Get the whitelist of allowed roles and permissions.

        Returns:
            Dictionary with allowed RBAC roles and Graph permissions.
        """
        return {
            "allowed_rbac_roles": sorted(ALLOWED_RBAC_ROLES),
            "blocked_rbac_roles": sorted(BLOCKED_RBAC_ROLES),
            "allowed_graph_permissions": sorted(ALLOWED_GRAPH_PERMISSIONS),
        }
