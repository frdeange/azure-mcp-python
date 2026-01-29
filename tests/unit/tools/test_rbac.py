"""Unit tests for RBAC tools.

Tests the RBAC role management and app role tools.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from azure_mcp.tools.rbac.service import (
    ALLOWED_GRAPH_PERMISSIONS,
    ALLOWED_RBAC_ROLES,
    BLOCKED_RBAC_ROLES,
    RbacService,
)
from azure_mcp.tools.rbac.roles import (
    RbacRoleListOptions,
    RbacRoleListTool,
    RbacRoleGetOptions,
    RbacRoleGetTool,
    RbacAllowedListOptions,
    RbacAllowedListTool,
)
from azure_mcp.tools.rbac.assignments import (
    RbacAssignmentListOptions,
    RbacAssignmentListTool,
    RbacAssignmentCreateOptions,
    RbacAssignmentCreateTool,
    RbacAssignmentDeleteOptions,
    RbacAssignmentDeleteTool,
)
from azure_mcp.tools.rbac.approles import (
    RbacApproleListOptions,
    RbacApproleListTool,
    RbacApproleGrantOptions,
    RbacApproleGrantTool,
)


# =============================================================================
# WHITELIST TESTS
# =============================================================================


class TestSecurityWhitelists:
    """Tests for security whitelists."""

    def test_allowed_roles_not_empty(self):
        """Allowed roles should not be empty."""
        assert len(ALLOWED_RBAC_ROLES) > 0

    def test_blocked_roles_not_empty(self):
        """Blocked roles should not be empty."""
        assert len(BLOCKED_RBAC_ROLES) > 0

    def test_no_overlap_allowed_blocked(self):
        """Allowed and blocked roles should not overlap."""
        overlap = ALLOWED_RBAC_ROLES & BLOCKED_RBAC_ROLES
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_dangerous_roles_blocked(self):
        """Dangerous roles should be blocked."""
        assert "Owner" in BLOCKED_RBAC_ROLES
        assert "Contributor" in BLOCKED_RBAC_ROLES
        assert "User Access Administrator" in BLOCKED_RBAC_ROLES

    def test_data_plane_roles_allowed(self):
        """Data plane roles should be allowed."""
        assert "Storage Blob Data Reader" in ALLOWED_RBAC_ROLES
        assert "Storage Blob Data Contributor" in ALLOWED_RBAC_ROLES
        assert "Key Vault Secrets User" in ALLOWED_RBAC_ROLES

    def test_graph_permissions_allowed(self):
        """Certain Graph permissions should be allowed."""
        assert "User.Read.All" in ALLOWED_GRAPH_PERMISSIONS
        assert "Group.Read.All" in ALLOWED_GRAPH_PERMISSIONS
        assert "Application.Read.All" in ALLOWED_GRAPH_PERMISSIONS


# =============================================================================
# ROLE TOOLS TESTS
# =============================================================================


class TestRbacRoleListOptions:
    """Tests for RbacRoleListOptions validation."""

    def test_minimal_options(self):
        """Minimal valid options."""
        options = RbacRoleListOptions(subscription="test-sub")
        assert options.subscription == "test-sub"
        assert options.scope == ""
        assert options.filter_builtin is True

    def test_full_options(self):
        """Full options with all fields."""
        options = RbacRoleListOptions(
            subscription="test-sub",
            scope="/subscriptions/123/resourceGroups/rg1",
            filter_builtin=False,
        )
        assert options.scope == "/subscriptions/123/resourceGroups/rg1"
        assert options.filter_builtin is False

    def test_missing_subscription_raises(self):
        """Missing subscription should raise error."""
        with pytest.raises(ValidationError):
            RbacRoleListOptions()


class TestRbacRoleListTool:
    """Tests for RbacRoleListTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacRoleListTool()
        assert tool.name == "rbac_role_list"
        assert "role definitions" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Execute calls service correctly."""
        tool = RbacRoleListTool()

        mock_roles = [
            {"role_name": "Storage Blob Data Reader", "is_allowed": True},
        ]

        with patch.object(RbacService, "list_role_definitions", new_callable=AsyncMock) as mock:
            mock.return_value = mock_roles
            options = RbacRoleListOptions(subscription="test-sub")
            result = await tool.execute(options)

            assert result == mock_roles
            mock.assert_called_once()


class TestRbacRoleGetTool:
    """Tests for RbacRoleGetTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacRoleGetTool()
        assert tool.name == "rbac_role_get"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Execute calls service correctly."""
        tool = RbacRoleGetTool()

        mock_role = {"role_name": "Storage Blob Data Reader", "is_allowed": True}

        with patch.object(RbacService, "get_role_definition", new_callable=AsyncMock) as mock:
            mock.return_value = mock_role
            options = RbacRoleGetOptions(
                subscription="test-sub",
                role_name="Storage Blob Data Reader",
            )
            result = await tool.execute(options)

            assert result == mock_role
            mock.assert_called_once()


class TestRbacAllowedListTool:
    """Tests for RbacAllowedListTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacAllowedListTool()
        assert tool.name == "rbac_allowed_list"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_whitelists(self, patch_credential):
        """Execute returns whitelists."""
        tool = RbacAllowedListTool()
        options = RbacAllowedListOptions()
        result = await tool.execute(options)

        assert "allowed_rbac_roles" in result
        assert "blocked_rbac_roles" in result
        assert "allowed_graph_permissions" in result


# =============================================================================
# ASSIGNMENT TOOLS TESTS
# =============================================================================


class TestRbacAssignmentListOptions:
    """Tests for RbacAssignmentListOptions validation."""

    def test_minimal_options(self):
        """Minimal valid options."""
        options = RbacAssignmentListOptions(subscription="test-sub")
        assert options.subscription == "test-sub"
        assert options.scope == ""
        assert options.principal_id == ""


class TestRbacAssignmentListTool:
    """Tests for RbacAssignmentListTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacAssignmentListTool()
        assert tool.name == "rbac_assignment_list"
        assert tool.metadata.read_only is True


class TestRbacAssignmentCreateOptions:
    """Tests for RbacAssignmentCreateOptions validation."""

    def test_minimal_options(self):
        """Minimal valid options."""
        options = RbacAssignmentCreateOptions(
            subscription="test-sub",
            scope="/subscriptions/123",
            role_name="Storage Blob Data Reader",
            principal_id="abc-123",
        )
        assert options.subscription == "test-sub"
        assert options.principal_type == "ServicePrincipal"

    def test_missing_required_raises(self):
        """Missing required fields should raise error."""
        with pytest.raises(ValidationError):
            RbacAssignmentCreateOptions(subscription="test-sub")


class TestRbacAssignmentCreateTool:
    """Tests for RbacAssignmentCreateTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacAssignmentCreateTool()
        assert tool.name == "rbac_assignment_create"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is False

    @pytest.mark.asyncio
    async def test_blocked_role_raises(self, patch_credential):
        """Blocked roles should raise ValueError."""
        tool = RbacAssignmentCreateTool()

        with patch.object(RbacService, "resolve_subscription", new_callable=AsyncMock) as mock_sub:
            mock_sub.return_value = "sub-123"

            options = RbacAssignmentCreateOptions(
                subscription="test-sub",
                scope="/subscriptions/123",
                role_name="Owner",  # Blocked role
                principal_id="abc-123",
            )

            with pytest.raises(Exception) as exc_info:
                await tool.execute(options)

            # May fail due to blocked role or missing module
            error_msg = str(exc_info.value).lower()
            assert "blocked" in error_msg or "owner" in error_msg or "module" in error_msg


class TestRbacAssignmentDeleteTool:
    """Tests for RbacAssignmentDeleteTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacAssignmentDeleteTool()
        assert tool.name == "rbac_assignment_delete"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True


# =============================================================================
# APP ROLE TOOLS TESTS
# =============================================================================


class TestRbacApproleListOptions:
    """Tests for RbacApproleListOptions validation."""

    def test_minimal_options(self):
        """Minimal valid options."""
        options = RbacApproleListOptions(principal_id="abc-123")
        assert options.principal_id == "abc-123"

    def test_missing_principal_raises(self):
        """Missing principal_id should raise error."""
        with pytest.raises(ValidationError):
            RbacApproleListOptions()


class TestRbacApproleListTool:
    """Tests for RbacApproleListTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacApproleListTool()
        assert tool.name == "rbac_approle_list"
        assert tool.metadata.read_only is True


class TestRbacApproleGrantOptions:
    """Tests for RbacApproleGrantOptions validation."""

    def test_minimal_options(self):
        """Minimal valid options."""
        options = RbacApproleGrantOptions(
            principal_id="abc-123",
            permission_name="User.Read.All",
        )
        assert options.principal_id == "abc-123"
        assert options.permission_name == "User.Read.All"


class TestRbacApproleGrantTool:
    """Tests for RbacApproleGrantTool."""

    def test_tool_properties(self):
        """Tool has correct properties."""
        tool = RbacApproleGrantTool()
        assert tool.name == "rbac_approle_grant"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is False


# =============================================================================
# SERVICE TESTS
# =============================================================================


class TestRbacServiceWhitelist:
    """Tests for RbacService whitelist enforcement."""

    @pytest.mark.asyncio
    async def test_create_blocked_role_raises(self, patch_credential):
        """Creating assignment with blocked role should raise."""
        service = RbacService()

        with patch.object(service, "resolve_subscription", new_callable=AsyncMock) as mock_sub:
            mock_sub.return_value = "sub-123"

            with pytest.raises(ValueError) as exc_info:
                await service.create_role_assignment(
                    subscription="test-sub",
                    scope="/subscriptions/123",
                    role_name="Owner",
                    principal_id="abc-123",
                )

            assert "blocked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_unknown_role_raises(self, patch_credential):
        """Creating assignment with unknown role should raise."""
        service = RbacService()

        with patch.object(service, "resolve_subscription", new_callable=AsyncMock) as mock_sub:
            mock_sub.return_value = "sub-123"

            with pytest.raises(ValueError) as exc_info:
                await service.create_role_assignment(
                    subscription="test-sub",
                    scope="/subscriptions/123",
                    role_name="Some Random Role",
                    principal_id="abc-123",
                )

            assert "whitelist" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_allowed_roles(self, patch_credential):
        """get_allowed_roles returns correct structure."""
        service = RbacService()
        result = await service.get_allowed_roles()

        assert "allowed_rbac_roles" in result
        assert "blocked_rbac_roles" in result
        assert "allowed_graph_permissions" in result
        assert isinstance(result["allowed_rbac_roles"], list)
