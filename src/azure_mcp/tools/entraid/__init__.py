"""Entra ID (Azure AD) tools.

Provides tools for interacting with Microsoft Entra ID via Microsoft Graph:
- User management (list, get, manager, direct reports, memberships, licenses)
- Group management (list, get, members, owners)
- Application management (apps, service principals)
- Security and audit (role assignments, directory roles, sign-in logs, audit logs)

Note: Some tools (signin_logs, audit_logs) require Entra ID P1 or P2 license.
"""

from azure_mcp.tools.entraid.app import (
    EntraidAppGetTool,
    EntraidAppListTool,
    EntraidServiceprincipalGetTool,
    EntraidServiceprincipalListTool,
)
from azure_mcp.tools.entraid.group import (
    EntraidGroupGetTool,
    EntraidGroupListTool,
    EntraidGroupMembersTool,
    EntraidGroupOwnersTool,
)
from azure_mcp.tools.entraid.security import (
    EntraidAuditLogsTool,
    EntraidDirectoryRolesTool,
    EntraidRoleAssignmentsTool,
    EntraidSigninLogsTool,
)
from azure_mcp.tools.entraid.user import (
    EntraidUserDirectreportsTool,
    EntraidUserGetTool,
    EntraidUserLicensesTool,
    EntraidUserListTool,
    EntraidUserManagerTool,
    EntraidUserMemberofTool,
)

__all__ = [
    # User tools
    "EntraidUserListTool",
    "EntraidUserGetTool",
    "EntraidUserManagerTool",
    "EntraidUserDirectreportsTool",
    "EntraidUserMemberofTool",
    "EntraidUserLicensesTool",
    # Group tools
    "EntraidGroupListTool",
    "EntraidGroupGetTool",
    "EntraidGroupMembersTool",
    "EntraidGroupOwnersTool",
    # App tools
    "EntraidAppListTool",
    "EntraidAppGetTool",
    "EntraidServiceprincipalListTool",
    "EntraidServiceprincipalGetTool",
    # Security tools
    "EntraidRoleAssignmentsTool",
    "EntraidDirectoryRolesTool",
    "EntraidSigninLogsTool",
    "EntraidAuditLogsTool",
]
