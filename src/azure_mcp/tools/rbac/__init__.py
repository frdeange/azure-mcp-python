"""RBAC tools for Azure role and permission management.

This module provides tools for:
- Listing and querying Azure RBAC role definitions
- Managing role assignments
- Managing Microsoft Graph app role assignments
"""

from azure_mcp.tools.rbac.roles import (
    RbacRoleListTool,
    RbacRoleGetTool,
    RbacAllowedListTool,
)
from azure_mcp.tools.rbac.assignments import (
    RbacAssignmentListTool,
    RbacAssignmentCreateTool,
    RbacAssignmentDeleteTool,
)
from azure_mcp.tools.rbac.approles import (
    RbacApproleListTool,
    RbacApproleGrantTool,
)

__all__ = [
    # Role definitions
    "RbacRoleListTool",
    "RbacRoleGetTool",
    "RbacAllowedListTool",
    # Role assignments
    "RbacAssignmentListTool",
    "RbacAssignmentCreateTool",
    "RbacAssignmentDeleteTool",
    # App roles (Graph)
    "RbacApproleListTool",
    "RbacApproleGrantTool",
]
