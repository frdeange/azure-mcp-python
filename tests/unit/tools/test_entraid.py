"""Tests for Entra ID tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from azure_mcp.tools.entraid.app import (
    EntraidAppGetOptions,
    EntraidAppGetTool,
    EntraidAppListOptions,
    EntraidAppListTool,
    EntraidServiceprincipalGetTool,
    EntraidServiceprincipalListTool,
)
from azure_mcp.tools.entraid.group import (
    EntraidGroupGetTool,
    EntraidGroupListOptions,
    EntraidGroupListTool,
    EntraidGroupMembersTool,
    EntraidGroupOwnersTool,
)
from azure_mcp.tools.entraid.security import (
    EntraidAuditLogsOptions,
    EntraidAuditLogsTool,
    EntraidDirectoryRolesTool,
    EntraidRoleAssignmentsTool,
    EntraidSigninLogsOptions,
    EntraidSigninLogsTool,
)
from azure_mcp.tools.entraid.service import (
    FULL_FIELDS,
    SECURITY_FIELDS,
    SUMMARY_FIELDS,
    EntraIdLicenseError,
    EntraIdService,
    get_user_fields,
)
from azure_mcp.tools.entraid.user import (
    EntraidUserDirectreportsOptions,
    EntraidUserDirectreportsTool,
    EntraidUserGetOptions,
    EntraidUserGetTool,
    EntraidUserLicensesTool,
    EntraidUserListOptions,
    EntraidUserListTool,
    EntraidUserManagerOptions,
    EntraidUserManagerTool,
    EntraidUserMemberofTool,
)


# =============================================================================
# EntraIdService Tests
# =============================================================================


class TestEntraIdServiceFieldConstants:
    """Tests for field constant functions."""

    def test_summary_fields_exist(self):
        """Test that summary fields are defined."""
        assert len(SUMMARY_FIELDS) > 0
        assert "id" in SUMMARY_FIELDS
        assert "displayName" in SUMMARY_FIELDS
        assert "userPrincipalName" in SUMMARY_FIELDS

    def test_full_fields_include_summary(self):
        """Test that full fields include key identity fields."""
        assert "id" in FULL_FIELDS
        assert "displayName" in FULL_FIELDS
        assert "department" in FULL_FIELDS
        assert "employeeId" in FULL_FIELDS

    def test_security_fields_are_security_focused(self):
        """Test that security fields include security-related properties."""
        assert "accountEnabled" in SECURITY_FIELDS
        assert "lastPasswordChangeDateTime" in SECURITY_FIELDS
        assert "userType" in SECURITY_FIELDS

    def test_get_user_fields_summary(self):
        """Test get_user_fields returns summary fields."""
        fields = get_user_fields("summary")
        assert fields == SUMMARY_FIELDS

    def test_get_user_fields_full(self):
        """Test get_user_fields returns full fields."""
        fields = get_user_fields("full")
        assert fields == FULL_FIELDS

    def test_get_user_fields_security(self):
        """Test get_user_fields returns security fields."""
        fields = get_user_fields("security")
        assert fields == SECURITY_FIELDS


class TestEntraIdLicenseError:
    """Tests for EntraIdLicenseError."""

    def test_license_error_message(self):
        """Test license error contains helpful message."""
        error = EntraIdLicenseError(
            "Operation requires P1/P2",
            operation="list_signin_logs",
        )
        assert "P1/P2" in str(error)
        assert error.operation == "list_signin_logs"

    def test_license_error_to_dict(self):
        """Test license error serialization."""
        error = EntraIdLicenseError(
            "Test error",
            operation="test_op",
        )
        result = error.to_dict()
        assert "license_info" in result
        assert "P1" in result["license_info"]
        assert result["operation"] == "test_op"


# =============================================================================
# User Tools Tests
# =============================================================================


class TestEntraidUserListOptions:
    """Tests for EntraidUserListOptions model."""

    def test_minimal_options(self):
        """Test creation with default values."""
        options = EntraidUserListOptions()
        assert options.filter_query == ""
        assert options.search == ""
        assert options.detail_level == "summary"
        assert options.top == 50

    def test_full_options(self):
        """Test creation with all fields."""
        options = EntraidUserListOptions(
            filter_query="department eq 'Engineering'",
            search="john",
            detail_level="full",
            top=100,
        )
        assert options.filter_query == "department eq 'Engineering'"
        assert options.search == "john"
        assert options.detail_level == "full"
        assert options.top == 100

    def test_detail_level_validation(self):
        """Test that detail_level only accepts valid values."""
        # Valid values should work
        EntraidUserListOptions(detail_level="summary")
        EntraidUserListOptions(detail_level="full")
        EntraidUserListOptions(detail_level="security")

        # Invalid value should raise
        with pytest.raises(ValueError):
            EntraidUserListOptions(detail_level="invalid")

    def test_top_validation(self):
        """Test that top must be between 1 and 999."""
        with pytest.raises(ValueError):
            EntraidUserListOptions(top=0)

        with pytest.raises(ValueError):
            EntraidUserListOptions(top=1000)


class TestEntraidUserListTool:
    """Tests for EntraidUserListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidUserListTool()
        assert tool.name == "entraid_user_list"
        assert "Entra ID" in tool.description or "Azure AD" in tool.description
        assert "User.Read.All" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    def test_options_schema(self):
        """Test that options schema is valid JSON schema."""
        tool = EntraidUserListTool()
        schema = tool.get_options_schema()

        assert "properties" in schema
        assert "detail_level" in schema["properties"]
        assert "top" in schema["properties"]

    def test_options_schema_no_anyof(self):
        """Test that schema doesn't contain anyOf (AI Foundry compatibility)."""
        tool = EntraidUserListTool()
        schema = tool.get_options_schema()

        # Check no anyOf in properties (would break AI Foundry)
        for prop_name, prop_def in schema.get("properties", {}).items():
            assert "anyOf" not in prop_def, f"Property {prop_name} contains anyOf"

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = EntraidUserListTool()
        options = EntraidUserListOptions(detail_level="summary", top=10)

        with patch.object(EntraIdService, "list_users") as mock_list:
            mock_list.return_value = [
                {"id": "user-1", "displayName": "John Doe", "userPrincipalName": "john@contoso.com"}
            ]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                filter_query="",
                search="",
                detail_level="summary",
                top=10,
            )
            assert len(result) == 1
            assert result[0]["displayName"] == "John Doe"


class TestEntraidUserGetOptions:
    """Tests for EntraidUserGetOptions model."""

    def test_required_user_id(self):
        """Test that user_id is required."""
        with pytest.raises(ValueError):
            EntraidUserGetOptions()

    def test_valid_options(self):
        """Test creation with valid options."""
        options = EntraidUserGetOptions(user_id="user@contoso.com")
        assert options.user_id == "user@contoso.com"
        assert options.detail_level == "summary"


class TestEntraidUserGetTool:
    """Tests for EntraidUserGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidUserGetTool()
        assert tool.name == "entraid_user_get"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = EntraidUserGetTool()
        options = EntraidUserGetOptions(user_id="user@contoso.com", detail_level="full")

        with patch.object(EntraIdService, "get_user") as mock_get:
            mock_get.return_value = {
                "id": "user-1",
                "displayName": "John Doe",
                "userPrincipalName": "user@contoso.com",
            }

            result = await tool.execute(options)

            mock_get.assert_called_once_with(
                user_id="user@contoso.com",
                detail_level="full",
            )
            assert result["displayName"] == "John Doe"


class TestEntraidUserManagerTool:
    """Tests for EntraidUserManagerTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidUserManagerTool()
        assert tool.name == "entraid_user_manager"
        assert "manager" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_manager(self, patch_credential):
        """Test that execute returns manager info."""
        tool = EntraidUserManagerTool()
        options = EntraidUserManagerOptions(user_id="user@contoso.com")

        with patch.object(EntraIdService, "get_user_manager") as mock_get:
            mock_get.return_value = {
                "id": "manager-1",
                "displayName": "Jane Manager",
            }

            result = await tool.execute(options)

            mock_get.assert_called_once_with(user_id="user@contoso.com")
            assert result["displayName"] == "Jane Manager"


class TestEntraidUserDirectreportsTool:
    """Tests for EntraidUserDirectreportsTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidUserDirectreportsTool()
        assert tool.name == "entraid_user_directreports"
        assert "direct report" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_reports(self, patch_credential):
        """Test that execute returns direct reports."""
        tool = EntraidUserDirectreportsTool()
        options = EntraidUserDirectreportsOptions(user_id="manager@contoso.com", top=10)

        with patch.object(EntraIdService, "get_user_direct_reports") as mock_get:
            mock_get.return_value = [
                {"id": "report-1", "displayName": "Report One"},
                {"id": "report-2", "displayName": "Report Two"},
            ]

            result = await tool.execute(options)

            mock_get.assert_called_once_with(user_id="manager@contoso.com", top=10)
            assert len(result) == 2


class TestEntraidUserMemberofTool:
    """Tests for EntraidUserMemberofTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidUserMemberofTool()
        assert tool.name == "entraid_user_memberof"
        assert "group" in tool.description.lower() or "role" in tool.description.lower()


class TestEntraidUserLicensesTool:
    """Tests for EntraidUserLicensesTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidUserLicensesTool()
        assert tool.name == "entraid_user_licenses"
        assert "license" in tool.description.lower()


# =============================================================================
# Group Tools Tests
# =============================================================================


class TestEntraidGroupListOptions:
    """Tests for EntraidGroupListOptions model."""

    def test_minimal_options(self):
        """Test creation with default values."""
        options = EntraidGroupListOptions()
        assert options.filter_query == ""
        assert options.search == ""
        assert options.detail_level == "summary"
        assert options.top == 50

    def test_detail_level_only_summary_full(self):
        """Test that group detail_level only accepts summary/full."""
        EntraidGroupListOptions(detail_level="summary")
        EntraidGroupListOptions(detail_level="full")

        # Security is not valid for groups
        with pytest.raises(ValueError):
            EntraidGroupListOptions(detail_level="security")


class TestEntraidGroupListTool:
    """Tests for EntraidGroupListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidGroupListTool()
        assert tool.name == "entraid_group_list"
        assert "Group.Read.All" in tool.description
        assert tool.metadata.read_only is True


class TestEntraidGroupGetTool:
    """Tests for EntraidGroupGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidGroupGetTool()
        assert tool.name == "entraid_group_get"


class TestEntraidGroupMembersTool:
    """Tests for EntraidGroupMembersTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidGroupMembersTool()
        assert tool.name == "entraid_group_members"
        assert "member" in tool.description.lower()


class TestEntraidGroupOwnersTool:
    """Tests for EntraidGroupOwnersTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidGroupOwnersTool()
        assert tool.name == "entraid_group_owners"
        assert "owner" in tool.description.lower()


# =============================================================================
# Application Tools Tests
# =============================================================================


class TestEntraidAppListOptions:
    """Tests for EntraidAppListOptions model."""

    def test_minimal_options(self):
        """Test creation with default values."""
        options = EntraidAppListOptions()
        assert options.filter_query == ""
        assert options.detail_level == "summary"
        assert options.top == 50


class TestEntraidAppListTool:
    """Tests for EntraidAppListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidAppListTool()
        assert tool.name == "entraid_app_list"
        assert "Application.Read.All" in tool.description
        assert tool.metadata.read_only is True


class TestEntraidAppGetOptions:
    """Tests for EntraidAppGetOptions model."""

    def test_required_app_id(self):
        """Test that app_id is required."""
        with pytest.raises(ValueError):
            EntraidAppGetOptions()


class TestEntraidAppGetTool:
    """Tests for EntraidAppGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidAppGetTool()
        assert tool.name == "entraid_app_get"
        assert "object id" in tool.description.lower()


class TestEntraidServiceprincipalListTool:
    """Tests for EntraidServiceprincipalListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidServiceprincipalListTool()
        assert tool.name == "entraid_serviceprincipal_list"
        assert "service principal" in tool.description.lower()


class TestEntraidServiceprincipalGetTool:
    """Tests for EntraidServiceprincipalGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidServiceprincipalGetTool()
        assert tool.name == "entraid_serviceprincipal_get"


# =============================================================================
# Security Tools Tests
# =============================================================================


class TestEntraidDirectoryRolesTool:
    """Tests for EntraidDirectoryRolesTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidDirectoryRolesTool()
        assert tool.name == "entraid_directory_roles"
        assert "RoleManagement.Read.Directory" in tool.description
        assert tool.metadata.read_only is True


class TestEntraidRoleAssignmentsTool:
    """Tests for EntraidRoleAssignmentsTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidRoleAssignmentsTool()
        assert tool.name == "entraid_role_assignments"
        assert "role" in tool.description.lower()


class TestEntraidSigninLogsOptions:
    """Tests for EntraidSigninLogsOptions model."""

    def test_minimal_options(self):
        """Test creation with default values."""
        options = EntraidSigninLogsOptions()
        assert options.user_id == ""
        assert options.app_id == ""
        assert options.filter_query == ""
        assert options.top == 50


class TestEntraidSigninLogsTool:
    """Tests for EntraidSigninLogsTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidSigninLogsTool()
        assert tool.name == "entraid_signin_logs"
        assert "P1" in tool.description or "P2" in tool.description
        assert "AuditLog.Read.All" in tool.description

    def test_description_warns_about_license(self):
        """Test that description warns about license requirement."""
        tool = EntraidSigninLogsTool()
        # Should warn users about premium license
        assert "REQUIRE" in tool.description.upper() or "LICENSE" in tool.description.upper()


class TestEntraidAuditLogsOptions:
    """Tests for EntraidAuditLogsOptions model."""

    def test_minimal_options(self):
        """Test creation with default values."""
        options = EntraidAuditLogsOptions()
        assert options.category == ""
        assert options.initiated_by == ""
        assert options.target_resource == ""
        assert options.top == 50


class TestEntraidAuditLogsTool:
    """Tests for EntraidAuditLogsTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = EntraidAuditLogsTool()
        assert tool.name == "entraid_audit_logs"
        assert "P1" in tool.description or "P2" in tool.description

    def test_description_warns_about_license(self):
        """Test that description warns about license requirement."""
        tool = EntraidAuditLogsTool()
        # Should warn users about premium license
        assert "REQUIRE" in tool.description.upper() or "LICENSE" in tool.description.upper()


# =============================================================================
# Schema Compatibility Tests (AI Foundry)
# =============================================================================


class TestEntraidSchemaCompatibility:
    """Tests for AI Foundry schema compatibility."""

    def test_user_list_no_optional_types(self):
        """Test that EntraidUserListOptions uses str = '' not str | None."""
        options = EntraidUserListOptions()
        # Should be empty string, not None
        assert options.filter_query == ""
        assert options.search == ""
        assert isinstance(options.filter_query, str)

    def test_group_list_no_optional_types(self):
        """Test that EntraidGroupListOptions uses str = '' not str | None."""
        options = EntraidGroupListOptions()
        assert options.filter_query == ""
        assert isinstance(options.filter_query, str)

    def test_app_list_no_optional_types(self):
        """Test that EntraidAppListOptions uses str = '' not str | None."""
        options = EntraidAppListOptions()
        assert options.filter_query == ""
        assert isinstance(options.filter_query, str)

    def test_signin_logs_no_optional_types(self):
        """Test that EntraidSigninLogsOptions uses str = '' not str | None."""
        options = EntraidSigninLogsOptions()
        assert options.user_id == ""
        assert options.app_id == ""
        assert isinstance(options.user_id, str)

    def test_all_tools_have_valid_schemas(self):
        """Test that all Entra ID tools produce valid schemas."""
        tools = [
            EntraidUserListTool(),
            EntraidUserGetTool(),
            EntraidUserManagerTool(),
            EntraidUserDirectreportsTool(),
            EntraidUserMemberofTool(),
            EntraidUserLicensesTool(),
            EntraidGroupListTool(),
            EntraidGroupGetTool(),
            EntraidGroupMembersTool(),
            EntraidGroupOwnersTool(),
            EntraidAppListTool(),
            EntraidAppGetTool(),
            EntraidServiceprincipalListTool(),
            EntraidServiceprincipalGetTool(),
            EntraidDirectoryRolesTool(),
            EntraidRoleAssignmentsTool(),
            EntraidSigninLogsTool(),
            EntraidAuditLogsTool(),
        ]

        for tool in tools:
            schema = tool.get_options_schema()
            assert "properties" in schema, f"{tool.name} missing properties"
            # Verify no $ref or $defs at top level
            assert "$ref" not in schema, f"{tool.name} has $ref (breaks AI Foundry)"
            assert "$defs" not in schema, f"{tool.name} has $defs (breaks AI Foundry)"
