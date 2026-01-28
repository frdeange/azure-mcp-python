"""Entra ID service layer.

Provides EntraIdService for Microsoft Graph operations using msgraph-sdk.
Uses AAD authentication via DefaultAzureCredential.
"""

from __future__ import annotations

from typing import Any, Literal

from azure_mcp.core.base import AzureService
from azure_mcp.core.errors import AuthorizationError, ToolError


# Field sets for different detail levels
# These define which user properties to fetch based on the requested detail level

SUMMARY_FIELDS = [
    "id",
    "displayName",
    "userPrincipalName",
    "mail",
    "jobTitle",
    "department",
    "accountEnabled",
    "userType",
    "createdDateTime",
]

FULL_FIELDS = [
    # Identity
    "id",
    "displayName",
    "givenName",
    "surname",
    "userPrincipalName",
    "mail",
    "mailNickname",
    "otherMails",
    "proxyAddresses",
    # Account Status
    "accountEnabled",
    "userType",
    "creationType",
    "createdDateTime",
    # Organization
    "jobTitle",
    "department",
    "companyName",
    "employeeId",
    "employeeType",
    "employeeHireDate",
    "officeLocation",
    # Contact
    "mobilePhone",
    "businessPhones",
    # Location
    "city",
    "state",
    "country",
    "postalCode",
    "streetAddress",
    "usageLocation",
    # Security
    "lastPasswordChangeDateTime",
    "passwordPolicies",
    # Sync
    "onPremisesSyncEnabled",
    "onPremisesLastSyncDateTime",
    "onPremisesSamAccountName",
    "onPremisesUserPrincipalName",
    # Guest
    "externalUserState",
    "externalUserStateChangeDateTime",
]

SECURITY_FIELDS = [
    "id",
    "displayName",
    "userPrincipalName",
    "accountEnabled",
    "signInActivity",
    "lastPasswordChangeDateTime",
    "createdDateTime",
    "creationType",
    "userType",
    "externalUserState",
    "onPremisesSyncEnabled",
    "onPremisesLastSyncDateTime",
    "passwordPolicies",
]

# Group field sets
GROUP_SUMMARY_FIELDS = [
    "id",
    "displayName",
    "description",
    "mail",
    "mailEnabled",
    "securityEnabled",
    "groupTypes",
    "membershipRule",
    "createdDateTime",
]

GROUP_FULL_FIELDS = [
    "id",
    "displayName",
    "description",
    "mail",
    "mailNickname",
    "mailEnabled",
    "securityEnabled",
    "groupTypes",
    "membershipRule",
    "membershipRuleProcessingState",
    "createdDateTime",
    "renewedDateTime",
    "expirationDateTime",
    "visibility",
    "onPremisesSyncEnabled",
    "onPremisesLastSyncDateTime",
    "onPremisesSamAccountName",
    "proxyAddresses",
    "isAssignableToRole",
]

# Application field sets
APP_SUMMARY_FIELDS = [
    "id",
    "appId",
    "displayName",
    "createdDateTime",
    "signInAudience",
]

APP_FULL_FIELDS = [
    "id",
    "appId",
    "displayName",
    "description",
    "createdDateTime",
    "signInAudience",
    "identifierUris",
    "publisherDomain",
    "web",
    "spa",
    "publicClient",
    "requiredResourceAccess",
    "passwordCredentials",
    "keyCredentials",
]

# Service Principal field sets
SP_SUMMARY_FIELDS = [
    "id",
    "appId",
    "displayName",
    "servicePrincipalType",
    "accountEnabled",
    "createdDateTime",
]

SP_FULL_FIELDS = [
    "id",
    "appId",
    "displayName",
    "description",
    "servicePrincipalType",
    "accountEnabled",
    "createdDateTime",
    "appOwnerOrganizationId",
    "appRoleAssignmentRequired",
    "loginUrl",
    "logoutUrl",
    "replyUrls",
    "servicePrincipalNames",
    "tags",
    "passwordCredentials",
    "keyCredentials",
]


class EntraIdLicenseError(ToolError):
    """Raised when an operation requires Entra ID P1/P2 license.

    Some Microsoft Graph operations (like sign-in logs and audit logs)
    require an Azure AD Premium license (P1 or P2).

    See: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins
    """

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.operation = operation

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.operation:
            result["operation"] = self.operation
        result["license_info"] = (
            "This operation requires an Entra ID P1 or P2 license. "
            "Sign-in logs and audit logs are premium features. "
            "See: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins"
        )
        return result


DetailLevel = Literal["summary", "full", "security"]


def get_user_fields(detail_level: DetailLevel) -> list[str]:
    """Get user fields for the specified detail level."""
    if detail_level == "full":
        return FULL_FIELDS
    elif detail_level == "security":
        return SECURITY_FIELDS
    return SUMMARY_FIELDS


def get_group_fields(detail_level: DetailLevel) -> list[str]:
    """Get group fields for the specified detail level."""
    if detail_level == "full":
        return GROUP_FULL_FIELDS
    return GROUP_SUMMARY_FIELDS


def get_app_fields(detail_level: DetailLevel) -> list[str]:
    """Get application fields for the specified detail level."""
    if detail_level == "full":
        return APP_FULL_FIELDS
    return APP_SUMMARY_FIELDS


def get_sp_fields(detail_level: DetailLevel) -> list[str]:
    """Get service principal fields for the specified detail level."""
    if detail_level == "full":
        return SP_FULL_FIELDS
    return SP_SUMMARY_FIELDS


def _serialize_graph_object(obj: Any) -> dict[str, Any]:
    """Serialize a Microsoft Graph object to a dictionary.

    The msgraph-sdk returns objects with properties, not dicts.
    This helper converts them to serializable dictionaries.
    """
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    # For msgraph objects, extract all non-private attributes
    result: dict[str, Any] = {}

    # Try to get the backing store if available (msgraph-sdk pattern)
    if hasattr(obj, "backing_store"):
        try:
            store = obj.backing_store
            if store:
                for key in store.enumerate_keys_for_values_changed_to_none():
                    result[key] = None
                # Get all stored values
                if hasattr(store, "get"):
                    for attr in dir(obj):
                        if not attr.startswith("_") and not callable(getattr(obj, attr, None)):
                            try:
                                value = getattr(obj, attr)
                                if value is not None:
                                    result[_to_camel_case(attr)] = _serialize_value(value)
                            except Exception:
                                pass
                    return result
        except Exception:
            pass

    # Fallback: iterate over public attributes
    for attr in dir(obj):
        if not attr.startswith("_") and not callable(getattr(obj, attr, None)):
            try:
                value = getattr(obj, attr)
                if value is not None and attr not in ("additional_data", "odata_type"):
                    result[_to_camel_case(attr)] = _serialize_value(value)
            except Exception:
                pass

    return result


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _serialize_value(value: Any) -> Any:
    """Serialize a value, handling nested objects and lists."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if hasattr(value, "isoformat"):
        return value.isoformat()
    # For complex objects, try to serialize
    if hasattr(value, "__dict__"):
        return _serialize_graph_object(value)
    return str(value)


class EntraIdService(AzureService):
    """
    Service for Microsoft Entra ID operations via Microsoft Graph.

    Uses msgraph-sdk with AAD authentication via DefaultAzureCredential.
    Requires appropriate Microsoft Graph permissions for each operation.

    Required Permissions:
    - User operations: User.Read.All
    - Group operations: Group.Read.All, GroupMember.Read.All
    - Application operations: Application.Read.All
    - Role operations: RoleManagement.Read.Directory
    - Audit logs: AuditLog.Read.All (requires P1/P2 license)
    """

    def _get_graph_client(self) -> Any:
        """Get Microsoft Graph client with authentication."""
        try:
            from msgraph import GraphServiceClient
        except ImportError as e:
            raise ToolError(
                "msgraph-sdk is not installed. Install it with: pip install azure-mcp[entra]"
            ) from e

        credential = self.get_credential()
        scopes = ["https://graph.microsoft.com/.default"]
        return GraphServiceClient(credentials=credential, scopes=scopes)

    def _handle_graph_error(self, error: Exception, operation: str) -> None:
        """Handle Microsoft Graph errors with descriptive messages."""
        error_str = str(error).lower()

        # Check for license-related errors (P1/P2 required)
        if any(term in error_str for term in ["license", "premium", "signins", "auditlogs"]):
            raise EntraIdLicenseError(
                f"Operation '{operation}' requires an Entra ID P1 or P2 license. "
                "Sign-in logs and audit logs are premium features.",
                operation=operation,
            ) from error

        # Check for permission errors
        if "forbidden" in error_str or "403" in error_str:
            raise AuthorizationError(
                f"Permission denied for '{operation}'. "
                "Ensure the application has the required Microsoft Graph permissions.",
                permission="Microsoft Graph API",
            ) from error

        # Re-raise other errors
        raise error

    # =========================================================================
    # User Operations
    # =========================================================================

    async def list_users(
        self,
        filter_query: str = "",
        search: str = "",
        detail_level: DetailLevel = "summary",
        top: int = 50,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        List users in Entra ID.

        Args:
            filter_query: OData filter expression (e.g., "department eq 'Engineering'").
            search: Search by displayName or mail (requires ConsistencyLevel header).
            detail_level: Level of detail ('summary', 'full', 'security').
            top: Maximum number of users to return.
            select: Specific fields to return (overrides detail_level).

        Returns:
            List of user dictionaries.
        """
        client = self._get_graph_client()
        fields = select or get_user_fields(detail_level)

        try:
            from msgraph.generated.users.users_request_builder import UsersRequestBuilder

            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
                top=top,
                select=fields,
                filter=filter_query if filter_query else None,
            )

            # Search requires special header
            request_config = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            if search:
                request_config.headers.add("ConsistencyLevel", "eventual")
                query_params.search = f'"displayName:{search}" OR "mail:{search}"'

            result = await client.users.get(request_configuration=request_config)

            users = []
            if result and result.value:
                for user in result.value:
                    users.append(_serialize_graph_object(user))

            return users

        except Exception as e:
            self._handle_graph_error(e, "list_users")
            raise

    async def get_user(
        self,
        user_id: str,
        detail_level: DetailLevel = "summary",
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get a specific user by ID or UPN.

        Args:
            user_id: User ID (GUID) or userPrincipalName.
            detail_level: Level of detail ('summary', 'full', 'security').
            select: Specific fields to return (overrides detail_level).

        Returns:
            User dictionary.
        """
        client = self._get_graph_client()
        fields = select or get_user_fields(detail_level)

        try:
            from msgraph.generated.users.item.user_item_request_builder import (
                UserItemRequestBuilder,
            )

            query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
                select=fields,
            )
            request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            result = await client.users.by_user_id(user_id).get(
                request_configuration=request_config
            )

            return _serialize_graph_object(result)

        except Exception as e:
            self._handle_graph_error(e, "get_user")
            raise

    async def get_user_manager(self, user_id: str) -> dict[str, Any]:
        """
        Get a user's manager.

        Args:
            user_id: User ID (GUID) or userPrincipalName.

        Returns:
            Manager user dictionary, or empty dict if no manager.
        """
        client = self._get_graph_client()

        try:
            result = await client.users.by_user_id(user_id).manager.get()

            if result:
                return _serialize_graph_object(result)
            return {}

        except Exception as e:
            # No manager is not an error
            if "404" in str(e) or "not found" in str(e).lower():
                return {}
            self._handle_graph_error(e, "get_user_manager")
            raise

    async def get_user_direct_reports(
        self,
        user_id: str,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get users who report directly to this user.

        Args:
            user_id: User ID (GUID) or userPrincipalName.
            top: Maximum number of reports to return.

        Returns:
            List of user dictionaries (direct reports).
        """
        client = self._get_graph_client()

        try:
            result = await client.users.by_user_id(user_id).direct_reports.get()

            reports = []
            if result and result.value:
                for report in result.value:
                    reports.append(_serialize_graph_object(report))

            return reports[:top]

        except Exception as e:
            self._handle_graph_error(e, "get_user_direct_reports")
            raise

    async def get_user_member_of(
        self,
        user_id: str,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get groups and directory roles the user is a member of.

        Args:
            user_id: User ID (GUID) or userPrincipalName.
            top: Maximum number of memberships to return.

        Returns:
            List of group/role dictionaries.
        """
        client = self._get_graph_client()

        try:
            result = await client.users.by_user_id(user_id).member_of.get()

            memberships = []
            if result and result.value:
                for membership in result.value:
                    memberships.append(_serialize_graph_object(membership))

            return memberships[:top]

        except Exception as e:
            self._handle_graph_error(e, "get_user_member_of")
            raise

    async def get_user_licenses(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get license details for a user.

        Args:
            user_id: User ID (GUID) or userPrincipalName.

        Returns:
            List of license detail dictionaries.
        """
        client = self._get_graph_client()

        try:
            result = await client.users.by_user_id(user_id).license_details.get()

            licenses = []
            if result and result.value:
                for license in result.value:
                    licenses.append(_serialize_graph_object(license))

            return licenses

        except Exception as e:
            self._handle_graph_error(e, "get_user_licenses")
            raise

    # =========================================================================
    # Group Operations
    # =========================================================================

    async def list_groups(
        self,
        filter_query: str = "",
        search: str = "",
        detail_level: DetailLevel = "summary",
        top: int = 50,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        List groups in Entra ID.

        Args:
            filter_query: OData filter expression.
            search: Search by displayName.
            detail_level: Level of detail ('summary', 'full').
            top: Maximum number of groups to return.
            select: Specific fields to return (overrides detail_level).

        Returns:
            List of group dictionaries.
        """
        client = self._get_graph_client()
        fields = select or get_group_fields(detail_level)

        try:
            from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder

            query_params = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
                top=top,
                select=fields,
                filter=filter_query if filter_query else None,
            )

            request_config = GroupsRequestBuilder.GroupsRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            if search:
                request_config.headers.add("ConsistencyLevel", "eventual")
                query_params.search = f'"displayName:{search}"'

            result = await client.groups.get(request_configuration=request_config)

            groups = []
            if result and result.value:
                for group in result.value:
                    groups.append(_serialize_graph_object(group))

            return groups

        except Exception as e:
            self._handle_graph_error(e, "list_groups")
            raise

    async def get_group(
        self,
        group_id: str,
        detail_level: DetailLevel = "summary",
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get a specific group by ID.

        Args:
            group_id: Group ID (GUID).
            detail_level: Level of detail ('summary', 'full').
            select: Specific fields to return (overrides detail_level).

        Returns:
            Group dictionary.
        """
        client = self._get_graph_client()
        fields = select or get_group_fields(detail_level)

        try:
            from msgraph.generated.groups.item.group_item_request_builder import (
                GroupItemRequestBuilder,
            )

            query_params = GroupItemRequestBuilder.GroupItemRequestBuilderGetQueryParameters(
                select=fields,
            )
            request_config = GroupItemRequestBuilder.GroupItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            result = await client.groups.by_group_id(group_id).get(
                request_configuration=request_config
            )

            return _serialize_graph_object(result)

        except Exception as e:
            self._handle_graph_error(e, "get_group")
            raise

    async def get_group_members(
        self,
        group_id: str,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get members of a group.

        Args:
            group_id: Group ID (GUID).
            top: Maximum number of members to return.

        Returns:
            List of member dictionaries (users, groups, service principals).
        """
        client = self._get_graph_client()

        try:
            result = await client.groups.by_group_id(group_id).members.get()

            members = []
            if result and result.value:
                for member in result.value:
                    members.append(_serialize_graph_object(member))

            return members[:top]

        except Exception as e:
            self._handle_graph_error(e, "get_group_members")
            raise

    async def get_group_owners(
        self,
        group_id: str,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get owners of a group.

        Args:
            group_id: Group ID (GUID).
            top: Maximum number of owners to return.

        Returns:
            List of owner dictionaries.
        """
        client = self._get_graph_client()

        try:
            result = await client.groups.by_group_id(group_id).owners.get()

            owners = []
            if result and result.value:
                for owner in result.value:
                    owners.append(_serialize_graph_object(owner))

            return owners[:top]

        except Exception as e:
            self._handle_graph_error(e, "get_group_owners")
            raise

    # =========================================================================
    # Application Operations
    # =========================================================================

    async def list_applications(
        self,
        filter_query: str = "",
        search: str = "",
        detail_level: DetailLevel = "summary",
        top: int = 50,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        List application registrations in Entra ID.

        Args:
            filter_query: OData filter expression.
            search: Search by displayName.
            detail_level: Level of detail ('summary', 'full').
            top: Maximum number of applications to return.
            select: Specific fields to return (overrides detail_level).

        Returns:
            List of application dictionaries.
        """
        client = self._get_graph_client()
        fields = select or get_app_fields(detail_level)

        try:
            from msgraph.generated.applications.applications_request_builder import (
                ApplicationsRequestBuilder,
            )

            query_params = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetQueryParameters(
                top=top,
                select=fields,
                filter=filter_query if filter_query else None,
            )

            request_config = (
                ApplicationsRequestBuilder.ApplicationsRequestBuilderGetRequestConfiguration(
                    query_parameters=query_params,
                )
            )

            if search:
                request_config.headers.add("ConsistencyLevel", "eventual")
                query_params.search = f'"displayName:{search}"'

            result = await client.applications.get(request_configuration=request_config)

            apps = []
            if result and result.value:
                for app in result.value:
                    apps.append(_serialize_graph_object(app))

            return apps

        except Exception as e:
            self._handle_graph_error(e, "list_applications")
            raise

    async def get_application(
        self,
        app_id: str,
        detail_level: DetailLevel = "summary",
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get a specific application by object ID.

        Args:
            app_id: Application object ID (GUID), NOT the appId.
            detail_level: Level of detail ('summary', 'full').
            select: Specific fields to return (overrides detail_level).

        Returns:
            Application dictionary.
        """
        client = self._get_graph_client()
        fields = select or get_app_fields(detail_level)

        try:
            from msgraph.generated.applications.item.application_item_request_builder import (
                ApplicationItemRequestBuilder,
            )

            query_params = (
                ApplicationItemRequestBuilder.ApplicationItemRequestBuilderGetQueryParameters(
                    select=fields,
                )
            )
            request_config = (
                ApplicationItemRequestBuilder.ApplicationItemRequestBuilderGetRequestConfiguration(
                    query_parameters=query_params,
                )
            )

            result = await client.applications.by_application_id(app_id).get(
                request_configuration=request_config
            )

            return _serialize_graph_object(result)

        except Exception as e:
            self._handle_graph_error(e, "get_application")
            raise

    async def list_service_principals(
        self,
        filter_query: str = "",
        search: str = "",
        detail_level: DetailLevel = "summary",
        top: int = 50,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        List service principals in Entra ID.

        Args:
            filter_query: OData filter expression.
            search: Search by displayName.
            detail_level: Level of detail ('summary', 'full').
            top: Maximum number of service principals to return.
            select: Specific fields to return (overrides detail_level).

        Returns:
            List of service principal dictionaries.
        """
        client = self._get_graph_client()
        fields = select or get_sp_fields(detail_level)

        try:
            from msgraph.generated.service_principals.service_principals_request_builder import (
                ServicePrincipalsRequestBuilder,
            )

            query_params = (
                ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
                    top=top,
                    select=fields,
                    filter=filter_query if filter_query else None,
                )
            )

            request_config = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            if search:
                request_config.headers.add("ConsistencyLevel", "eventual")
                query_params.search = f'"displayName:{search}"'

            result = await client.service_principals.get(request_configuration=request_config)

            sps = []
            if result and result.value:
                for sp in result.value:
                    sps.append(_serialize_graph_object(sp))

            return sps

        except Exception as e:
            self._handle_graph_error(e, "list_service_principals")
            raise

    async def get_service_principal(
        self,
        sp_id: str,
        detail_level: DetailLevel = "summary",
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get a specific service principal by object ID.

        Args:
            sp_id: Service principal object ID (GUID).
            detail_level: Level of detail ('summary', 'full').
            select: Specific fields to return (overrides detail_level).

        Returns:
            Service principal dictionary.
        """
        client = self._get_graph_client()
        fields = select or get_sp_fields(detail_level)

        try:
            from msgraph.generated.service_principals.item.service_principal_item_request_builder import (
                ServicePrincipalItemRequestBuilder,
            )

            query_params = ServicePrincipalItemRequestBuilder.ServicePrincipalItemRequestBuilderGetQueryParameters(
                select=fields,
            )
            request_config = ServicePrincipalItemRequestBuilder.ServicePrincipalItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            result = await client.service_principals.by_service_principal_id(sp_id).get(
                request_configuration=request_config
            )

            return _serialize_graph_object(result)

        except Exception as e:
            self._handle_graph_error(e, "get_service_principal")
            raise

    # =========================================================================
    # Security & Audit Operations
    # =========================================================================

    async def list_directory_roles(
        self,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List activated directory roles in Entra ID.

        Args:
            top: Maximum number of roles to return.

        Returns:
            List of directory role dictionaries.
        """
        client = self._get_graph_client()

        try:
            result = await client.directory_roles.get()

            roles = []
            if result and result.value:
                for role in result.value:
                    roles.append(_serialize_graph_object(role))

            return roles[:top]

        except Exception as e:
            self._handle_graph_error(e, "list_directory_roles")
            raise

    async def list_role_assignments(
        self,
        principal_id: str = "",
        role_definition_id: str = "",
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List role assignments in Entra ID.

        Args:
            principal_id: Filter by principal (user/group/SP) ID.
            role_definition_id: Filter by role definition ID.
            top: Maximum number of assignments to return.

        Returns:
            List of role assignment dictionaries.
        """
        client = self._get_graph_client()

        try:
            from msgraph.generated.role_management.directory.role_assignments.role_assignments_request_builder import (
                RoleAssignmentsRequestBuilder,
            )

            # Build filter
            filters = []
            if principal_id:
                filters.append(f"principalId eq '{principal_id}'")
            if role_definition_id:
                filters.append(f"roleDefinitionId eq '{role_definition_id}'")

            filter_str = " and ".join(filters) if filters else None

            query_params = (
                RoleAssignmentsRequestBuilder.RoleAssignmentsRequestBuilderGetQueryParameters(
                    top=top,
                    filter=filter_str,
                    expand=["principal", "roleDefinition"],
                )
            )
            request_config = (
                RoleAssignmentsRequestBuilder.RoleAssignmentsRequestBuilderGetRequestConfiguration(
                    query_parameters=query_params,
                )
            )

            result = await client.role_management.directory.role_assignments.get(
                request_configuration=request_config
            )

            assignments = []
            if result and result.value:
                for assignment in result.value:
                    assignments.append(_serialize_graph_object(assignment))

            return assignments

        except Exception as e:
            self._handle_graph_error(e, "list_role_assignments")
            raise

    async def list_signin_logs(
        self,
        user_id: str = "",
        app_id: str = "",
        filter_query: str = "",
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List sign-in logs from Entra ID.

        NOTE: This operation requires an Entra ID P1 or P2 license.

        Args:
            user_id: Filter by user ID.
            app_id: Filter by application ID.
            filter_query: Additional OData filter expression.
            top: Maximum number of logs to return.

        Returns:
            List of sign-in log dictionaries.

        Raises:
            EntraIdLicenseError: If the tenant doesn't have P1/P2 license.
        """
        client = self._get_graph_client()

        try:
            from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import (
                SignInsRequestBuilder,
            )

            # Build filter
            filters = []
            if user_id:
                filters.append(f"userId eq '{user_id}'")
            if app_id:
                filters.append(f"appId eq '{app_id}'")
            if filter_query:
                filters.append(filter_query)

            filter_str = " and ".join(filters) if filters else None

            query_params = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
                top=top,
                filter=filter_str,
                orderby=["createdDateTime desc"],
            )
            request_config = SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )

            result = await client.audit_logs.sign_ins.get(request_configuration=request_config)

            logs = []
            if result and result.value:
                for log in result.value:
                    logs.append(_serialize_graph_object(log))

            return logs

        except Exception as e:
            self._handle_graph_error(e, "list_signin_logs")
            raise

    async def list_audit_logs(
        self,
        category: str = "",
        initiated_by: str = "",
        target_resource: str = "",
        filter_query: str = "",
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List directory audit logs from Entra ID.

        NOTE: This operation requires an Entra ID P1 or P2 license.

        Args:
            category: Filter by activity category.
            initiated_by: Filter by initiator ID.
            target_resource: Filter by target resource ID.
            filter_query: Additional OData filter expression.
            top: Maximum number of logs to return.

        Returns:
            List of audit log dictionaries.

        Raises:
            EntraIdLicenseError: If the tenant doesn't have P1/P2 license.
        """
        client = self._get_graph_client()

        try:
            from msgraph.generated.audit_logs.directory_audits.directory_audits_request_builder import (
                DirectoryAuditsRequestBuilder,
            )

            # Build filter
            filters = []
            if category:
                filters.append(f"category eq '{category}'")
            if initiated_by:
                filters.append(f"initiatedBy/user/id eq '{initiated_by}'")
            if target_resource:
                filters.append(f"targetResources/any(t: t/id eq '{target_resource}')")
            if filter_query:
                filters.append(filter_query)

            filter_str = " and ".join(filters) if filters else None

            query_params = (
                DirectoryAuditsRequestBuilder.DirectoryAuditsRequestBuilderGetQueryParameters(
                    top=top,
                    filter=filter_str,
                    orderby=["activityDateTime desc"],
                )
            )
            request_config = (
                DirectoryAuditsRequestBuilder.DirectoryAuditsRequestBuilderGetRequestConfiguration(
                    query_parameters=query_params,
                )
            )

            result = await client.audit_logs.directory_audits.get(
                request_configuration=request_config
            )

            logs = []
            if result and result.value:
                for log in result.value:
                    logs.append(_serialize_graph_object(log))

            return logs

        except Exception as e:
            self._handle_graph_error(e, "list_audit_logs")
            raise
