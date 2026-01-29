"""Architecture pattern validation tests.

These tests enforce architectural constraints to prevent common pattern violations.
They scan the codebase to ensure developers use base class methods instead of
implementing SDK clients directly.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# Paths
SRC_ROOT = Path(__file__).parent.parent.parent / "src" / "azure_mcp"
TOOLS_ROOT = SRC_ROOT / "tools"
CORE_ROOT = SRC_ROOT / "core"


class TestResourceGraphPatterns:
    """Ensure ResourceGraphClient is only used in base.py."""

    # Files that ARE allowed to import ResourceGraphClient
    ALLOWED_FILES = {
        CORE_ROOT / "base.py",
    }

    def test_resource_graph_client_only_in_base(self):
        """ResourceGraphClient should only be imported in core/base.py.

        All services should use self.execute_resource_graph_query() from AzureService
        instead of creating ResourceGraphClient directly.

        If this test fails, refactor your service to use the base class method:

            # ❌ WRONG - Don't do this
            from azure.mgmt.resourcegraph import ResourceGraphClient
            client = ResourceGraphClient(credential)
            result = client.resources(request)

            # ✅ CORRECT - Use base class method
            result = await self.execute_resource_graph_query(
                query=kql_query,
                subscriptions=[sub_id],
            )
        """
        violations = []

        for py_file in SRC_ROOT.rglob("*.py"):
            if py_file in self.ALLOWED_FILES:
                continue

            content = py_file.read_text()

            # Check for import of ResourceGraphClient (not just comments)
            if "ResourceGraphClient" in content and re.search(
                r"^\s*(from|import).*ResourceGraphClient", content, re.MULTILINE
            ):
                violations.append(str(py_file.relative_to(SRC_ROOT)))

        assert not violations, (
            "ResourceGraphClient should only be imported in core/base.py.\n"
            "Found violations in:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nUse self.execute_resource_graph_query() instead. See docs/adding-tools.md"
        )


class TestSubscriptionClientPatterns:
    """Ensure SubscriptionClient is only used in base.py."""

    ALLOWED_FILES = {
        CORE_ROOT / "base.py",
    }

    def test_subscription_client_only_in_base(self):
        """SubscriptionClient should only be imported in core/base.py.

        All services should use self.resolve_subscription() or self.list_subscriptions()
        from AzureService instead of creating SubscriptionClient directly.

        If this test fails, refactor your service to use the base class method:

            # ❌ WRONG - Don't do this
            from azure.mgmt.resource import SubscriptionClient
            client = SubscriptionClient(credential)
            for sub in client.subscriptions.list(): ...

            # ✅ CORRECT - Use base class methods
            sub_id = await self.resolve_subscription(subscription_name_or_id)
            all_subs = await self.list_subscriptions()
        """
        violations = []

        for py_file in SRC_ROOT.rglob("*.py"):
            if py_file in self.ALLOWED_FILES:
                continue

            content = py_file.read_text()

            if "SubscriptionClient" in content and re.search(
                r"^\s*(from|import).*SubscriptionClient", content, re.MULTILINE
            ):
                violations.append(str(py_file.relative_to(SRC_ROOT)))

        assert not violations, (
            "SubscriptionClient should only be imported in core/base.py.\n"
            "Found violations in:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nUse self.resolve_subscription() or self.list_subscriptions() instead."
        )


class TestCredentialPatterns:
    """Ensure credentials are obtained through CredentialProvider or base class."""

    ALLOWED_FILES = {
        CORE_ROOT / "auth.py",
        CORE_ROOT / "base.py",
    }

    def test_default_azure_credential_centralized(self):
        """DefaultAzureCredential should only be created in core/auth.py or base.py.

        All services should use self.get_credential() from AzureService instead of
        creating DefaultAzureCredential directly.

        If this test fails, refactor your service:

            # ❌ WRONG - Don't do this
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()

            # ✅ CORRECT - Use base class method
            credential = self.get_credential()
        """
        violations = []

        for py_file in SRC_ROOT.rglob("*.py"):
            if py_file in self.ALLOWED_FILES:
                continue

            content = py_file.read_text()

            # Check for instantiation of DefaultAzureCredential
            # We allow imports but not instantiation (DefaultAzureCredential())
            if "DefaultAzureCredential()" in content:
                violations.append(str(py_file.relative_to(SRC_ROOT)))

        assert not violations, (
            "DefaultAzureCredential() should only be instantiated in core/auth.py.\n"
            "Found violations in:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nUse self.get_credential() from AzureService instead."
        )


class TestServiceInheritance:
    """Ensure all service classes extend AzureService."""

    def test_all_services_extend_azure_service(self):
        """All *Service classes in tools/ should extend AzureService.

        This ensures all services have access to base class methods like
        execute_resource_graph_query(), resolve_subscription(), get_credential(), etc.
        """
        violations = []

        for py_file in TOOLS_ROOT.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.endswith("Service"):
                    base_names = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_names.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_names.append(base.attr)

                    if "AzureService" not in base_names:
                        violations.append(f"{py_file.relative_to(TOOLS_ROOT)}: {node.name}")

        assert not violations, (
            "All *Service classes should extend AzureService.\n"
            "Found violations:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nChange 'class MyService:' to 'class MyService(AzureService):'"
        )


class TestToolInheritance:
    """Ensure all tool classes extend AzureTool."""

    def test_all_tools_extend_azure_tool(self):
        """All *Tool classes in tools/ should extend AzureTool.

        This ensures consistent tool structure and enables automatic registration.
        """
        violations = []

        for py_file in TOOLS_ROOT.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.endswith("Tool"):
                    base_names = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_names.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_names.append(base.attr)

                    if "AzureTool" not in base_names:
                        violations.append(f"{py_file.relative_to(TOOLS_ROOT)}: {node.name}")

        assert not violations, (
            "All *Tool classes should extend AzureTool.\n"
            "Found violations:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nChange 'class MyTool:' to 'class MyTool(AzureTool):'"
        )


class TestToolRegistration:
    """Ensure all Tool classes are decorated with @register_tool."""

    def test_all_tools_have_register_decorator(self):
        """All *Tool classes should have @register_tool decorator.

        This ensures tools are automatically discovered and registered.
        """
        violations = []

        for py_file in TOOLS_ROOT.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.endswith("Tool"):
                    has_register = any(
                        (
                            isinstance(d, ast.Call)
                            and isinstance(d.func, ast.Name)
                            and d.func.id == "register_tool"
                        )
                        or (isinstance(d, ast.Name) and d.id == "register_tool")
                        for d in node.decorator_list
                    )

                    if not has_register:
                        violations.append(f"{py_file.relative_to(TOOLS_ROOT)}: {node.name}")

        assert not violations, (
            "All *Tool classes should have @register_tool decorator.\n"
            "Found violations:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nAdd @register_tool('family', 'subgroup') before the class definition."
        )
