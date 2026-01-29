"""Tests for JSON schema compatibility with Azure AI Foundry.

Azure AI Foundry does NOT support anyOf, allOf, or oneOf in JSON schemas.
These tests verify that all tool options models generate compatible schemas.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from azure_mcp.core.registry import registry


def check_schema_compatibility(schema: dict, path: str = "") -> list[str]:
    """
    Recursively check a JSON schema for AI Foundry incompatibilities.

    Returns a list of error messages for any incompatibilities found.
    """
    errors = []

    if not isinstance(schema, dict):
        return errors

    # Check for forbidden patterns
    forbidden_keys = ["anyOf", "allOf", "oneOf"]
    for key in forbidden_keys:
        if key in schema:
            errors.append(f"{path}: contains '{key}' which is not supported by AI Foundry")

    # Recursively check nested structures
    for key, value in schema.items():
        new_path = f"{path}.{key}" if path else key

        if isinstance(value, dict):
            errors.extend(check_schema_compatibility(value, new_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    errors.extend(check_schema_compatibility(item, f"{new_path}[{i}]"))

    return errors


class TestSchemaCompatibility:
    """Test that all tool schemas are AI Foundry compatible."""

    def test_all_tool_schemas_are_foundry_compatible(self):
        """
        Verify no tool generates anyOf, allOf, or oneOf in its JSON schema.

        This test prevents regressions where someone adds a new tool with
        Optional[str] or str | None patterns that generate incompatible schemas.
        """
        # Import tools to trigger registration
        from azure_mcp import tools  # noqa: F401

        all_errors = []

        for tool in registry.list_tools():
            options_model = tool.options_model
            schema = options_model.model_json_schema()

            errors = check_schema_compatibility(schema)

            if errors:
                all_errors.append(f"\n{tool.name} ({options_model.__name__}):")
                all_errors.extend(f"  - {e}" for e in errors)

        if all_errors:
            error_msg = (
                "The following tools have schemas incompatible with Azure AI Foundry:\n"
                + "\n".join(all_errors)
                + "\n\nFix: Change 'str | None = None' to 'str = \"\"' and "
                "'list | None = None' to 'list = Field(default_factory=list)'\n"
                "See docs/ai-foundry-deployment.md for details."
            )
            pytest.fail(error_msg)

    def test_incompatible_schema_detected(self):
        """Verify the check function catches incompatible patterns."""

        # Schema with anyOf (what Pydantic generates for Optional types)
        incompatible_schema = {
            "properties": {
                "name": {"type": "string"},
                "optional_field": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                },
            }
        }

        errors = check_schema_compatibility(incompatible_schema)
        assert len(errors) == 1
        assert "anyOf" in errors[0]

    def test_compatible_schema_passes(self):
        """Verify compatible schemas pass validation."""

        compatible_schema = {
            "properties": {
                "name": {"type": "string"},
                "optional_field": {
                    "type": "string",
                    "default": "",
                },
                "optional_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "default": [],
                },
            }
        }

        errors = check_schema_compatibility(compatible_schema)
        assert len(errors) == 0

    def test_allof_detected(self):
        """Verify allOf patterns are detected."""
        schema = {
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
                {"type": "object", "properties": {"b": {"type": "string"}}},
            ]
        }

        errors = check_schema_compatibility(schema)
        assert len(errors) == 1
        assert "allOf" in errors[0]

    def test_oneof_detected(self):
        """Verify oneOf patterns are detected."""
        schema = {"properties": {"value": {"oneOf": [{"type": "string"}, {"type": "integer"}]}}}

        errors = check_schema_compatibility(schema)
        assert len(errors) == 1
        assert "oneOf" in errors[0]


class TestSpecificToolSchemas:
    """Test specific tools that previously had issues."""

    def test_cosmos_account_list_schema(self):
        """Verify cosmos_account_list has compatible schema."""
        from azure_mcp.tools.cosmos.account import CosmosAccountListOptions

        schema = CosmosAccountListOptions.model_json_schema()
        errors = check_schema_compatibility(schema)

        assert len(errors) == 0, f"Schema errors: {errors}"

        # Verify resource_group uses string with empty default
        props = schema.get("properties", {})
        rg = props.get("resource_group", {})
        assert rg.get("type") == "string"
        assert rg.get("default") == ""

    def test_cosmos_item_query_schema(self):
        """Verify cosmos_item_query has compatible schema."""
        from azure_mcp.tools.cosmos.item import CosmosItemQueryOptions

        schema = CosmosItemQueryOptions.model_json_schema()
        errors = check_schema_compatibility(schema)

        assert len(errors) == 0, f"Schema errors: {errors}"

        # Verify parameters uses array type (not anyOf with null)
        props = schema.get("properties", {})
        params = props.get("parameters", {})
        assert params.get("type") == "array"
        # default_factory generates empty list at runtime, may not appear in schema
        assert "anyOf" not in params, "parameters should not have anyOf"


class TestDefaultFactoryNotRequired:
    """Test that fields with default_factory are not marked as required."""

    def test_resourcegraph_list_fields_not_required(self):
        """Verify subscriptions and management_groups are NOT required in schema."""
        from azure_mcp.tools.resourcegraph.query import ResourceGraphQueryOptions

        schema = ResourceGraphQueryOptions.model_json_schema()
        required = schema.get("required", [])

        # query IS required (has ...)
        assert "query" in required, "query should be required"

        # subscriptions and management_groups have default_factory=list
        # so should NOT be required
        assert "subscriptions" not in required, (
            "subscriptions has default_factory=list, should NOT be required"
        )
        assert "management_groups" not in required, (
            "management_groups has default_factory=list, should NOT be required"
        )

    def test_pydantic_schema_vs_mcp_schema(self):
        """Verify Pydantic's native schema correctly marks defaults."""
        from azure_mcp.tools.resourcegraph.query import ResourceGraphQueryOptions

        # Pydantic's own schema should be correct
        schema = ResourceGraphQueryOptions.model_json_schema()
        required = schema.get("required", [])

        # Fields with default_factory should NOT appear in required
        props = schema.get("properties", {})

        # subscriptions should have a default (empty array)
        subs = props.get("subscriptions", {})
        assert subs.get("type") == "array", "subscriptions should be array type"

        # It should not be in required
        assert "subscriptions" not in required

    def test_all_default_factory_fields_not_required(self):
        """Check all tools to ensure default_factory fields are optional."""
        from azure_mcp import tools  # noqa: F401

        violations = []

        for tool in registry.list_tools():
            options_model = tool.options_model
            schema = options_model.model_json_schema()
            required = set(schema.get("required", []))

            # Check each field
            for field_name, field_info in options_model.model_fields.items():
                if field_info.default_factory is not None:
                    # Field has default_factory, should NOT be required
                    if field_name in required:
                        violations.append(
                            f"{tool.name}: {field_name} has default_factory but is marked required"
                        )

        assert not violations, "Fields with default_factory should not be required:\n" + "\n".join(
            f"  - {v}" for v in violations
        )
