"""Unit tests for Cost Management tools.

Tests all 7 Cost Management tools:
- cost_query
- cost_forecast
- cost_budgets_list
- cost_budgets_get
- cost_recommendations
- cost_exports_list
- cost_usage_by_resource
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from azure_mcp.tools.cost.budgets import (
    CostBudgetsGetOptions,
    CostBudgetsGetTool,
    CostBudgetsListOptions,
    CostBudgetsListTool,
)
from azure_mcp.tools.cost.exports import CostExportsListOptions, CostExportsListTool
from azure_mcp.tools.cost.forecast import CostForecastOptions, CostForecastTool
from azure_mcp.tools.cost.query import CostQueryOptions, CostQueryTool
from azure_mcp.tools.cost.recommendations import (
    CostRecommendationsOptions,
    CostRecommendationsTool,
)
from azure_mcp.tools.cost.usage import CostUsageByResourceOptions, CostUsageByResourceTool


# =============================================================================
# CostQueryOptions Tests
# =============================================================================


class TestCostQueryOptions:
    """Tests for CostQueryOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = CostQueryOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""
        assert options.timeframe == "MonthToDate"
        assert options.granularity == "None"
        assert options.group_by == ""
        assert options.metric_type == "ActualCost"

    def test_full_options(self):
        """Test with all fields specified."""
        options = CostQueryOptions(
            subscription="my-sub",
            resource_group="my-rg",
            timeframe="TheLastMonth",
            granularity="Daily",
            group_by="ResourceGroup",
            metric_type="AmortizedCost",
        )
        assert options.subscription == "my-sub"
        assert options.resource_group == "my-rg"
        assert options.timeframe == "TheLastMonth"
        assert options.granularity == "Daily"
        assert options.group_by == "ResourceGroup"
        assert options.metric_type == "AmortizedCost"

    def test_invalid_timeframe(self):
        """Test that invalid timeframe is rejected."""
        with pytest.raises(ValidationError):
            CostQueryOptions(subscription="my-sub", timeframe="Invalid")

    def test_invalid_granularity(self):
        """Test that invalid granularity is rejected."""
        with pytest.raises(ValidationError):
            CostQueryOptions(subscription="my-sub", granularity="Weekly")


# =============================================================================
# CostQueryTool Tests
# =============================================================================


class TestCostQueryTool:
    """Tests for CostQueryTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostQueryTool()
        assert tool.name == "cost_query"
        assert "cost data" in tool.description.lower()
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    def test_options_schema(self):
        """Test that options schema is valid JSON schema."""
        tool = CostQueryTool()
        schema = tool.get_options_schema()

        assert "properties" in schema
        assert "subscription" in schema["properties"]
        assert "timeframe" in schema["properties"]
        assert "granularity" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostQueryTool()
        options = CostQueryOptions(
            subscription="my-sub",
            timeframe="MonthToDate",
            granularity="Daily",
            group_by="ResourceGroup",
        )

        mock_result = {
            "columns": [{"name": "Cost", "type": "Number"}],
            "rows": [[100.0]],
            "scope": "/subscriptions/123",
        }

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.query_costs",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert result["columns"][0]["name"] == "Cost"
        assert result["rows"][0][0] == 100.0


# =============================================================================
# CostForecastOptions Tests
# =============================================================================


class TestCostForecastOptions:
    """Tests for CostForecastOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = CostForecastOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.forecast_days == 30
        assert options.granularity == "Daily"

    def test_forecast_days_validation(self):
        """Test forecast_days range validation."""
        # Valid range
        options = CostForecastOptions(subscription="my-sub", forecast_days=90)
        assert options.forecast_days == 90

        # Too low
        with pytest.raises(ValidationError):
            CostForecastOptions(subscription="my-sub", forecast_days=0)

        # Too high
        with pytest.raises(ValidationError):
            CostForecastOptions(subscription="my-sub", forecast_days=400)


# =============================================================================
# CostForecastTool Tests
# =============================================================================


class TestCostForecastTool:
    """Tests for CostForecastTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostForecastTool()
        assert tool.name == "cost_forecast"
        assert "forecast" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostForecastTool()
        options = CostForecastOptions(subscription="my-sub", forecast_days=14)

        mock_result = {
            "columns": [{"name": "Cost", "type": "Number"}],
            "rows": [[150.0]],
            "forecast_days": 14,
        }

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.get_forecast",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert result["forecast_days"] == 14


# =============================================================================
# CostUsageByResourceOptions Tests
# =============================================================================


class TestCostUsageByResourceOptions:
    """Tests for CostUsageByResourceOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = CostUsageByResourceOptions(subscription="my-sub")
        assert options.top == 20
        assert options.timeframe == "MonthToDate"

    def test_top_validation(self):
        """Test top parameter validation."""
        # Valid range
        options = CostUsageByResourceOptions(subscription="my-sub", top=50)
        assert options.top == 50

        # Too low
        with pytest.raises(ValidationError):
            CostUsageByResourceOptions(subscription="my-sub", top=0)

        # Too high
        with pytest.raises(ValidationError):
            CostUsageByResourceOptions(subscription="my-sub", top=200)


# =============================================================================
# CostUsageByResourceTool Tests
# =============================================================================


class TestCostUsageByResourceTool:
    """Tests for CostUsageByResourceTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostUsageByResourceTool()
        assert tool.name == "cost_usage_by_resource"
        assert "resource" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostUsageByResourceTool()
        options = CostUsageByResourceOptions(subscription="my-sub", top=10)

        mock_result = [
            {"resource_id": "/subscriptions/123/vm1", "cost": 100.0},
            {"resource_id": "/subscriptions/123/vm2", "cost": 50.0},
        ]

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.query_costs_by_resource",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 2
        assert result[0]["cost"] == 100.0


# =============================================================================
# CostBudgetsListOptions Tests
# =============================================================================


class TestCostBudgetsListOptions:
    """Tests for CostBudgetsListOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = CostBudgetsListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""


# =============================================================================
# CostBudgetsListTool Tests
# =============================================================================


class TestCostBudgetsListTool:
    """Tests for CostBudgetsListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostBudgetsListTool()
        assert tool.name == "cost_budgets_list"
        assert "budget" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostBudgetsListTool()
        options = CostBudgetsListOptions(subscription="my-sub")

        mock_result = [
            {"name": "monthly-budget", "amount": 1000, "current_spend": 500},
        ]

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.list_budgets",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 1
        assert result[0]["name"] == "monthly-budget"


# =============================================================================
# CostBudgetsGetOptions Tests
# =============================================================================


class TestCostBudgetsGetOptions:
    """Tests for CostBudgetsGetOptions validation."""

    def test_required_fields(self):
        """Test that subscription and budget_name are required."""
        options = CostBudgetsGetOptions(subscription="my-sub", budget_name="my-budget")
        assert options.subscription == "my-sub"
        assert options.budget_name == "my-budget"

    def test_missing_budget_name(self):
        """Test that missing budget_name raises error."""
        with pytest.raises(ValidationError):
            CostBudgetsGetOptions(subscription="my-sub")


# =============================================================================
# CostBudgetsGetTool Tests
# =============================================================================


class TestCostBudgetsGetTool:
    """Tests for CostBudgetsGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostBudgetsGetTool()
        assert tool.name == "cost_budgets_get"
        assert "budget" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostBudgetsGetTool()
        options = CostBudgetsGetOptions(subscription="my-sub", budget_name="my-budget")

        mock_result = {
            "name": "my-budget",
            "amount": 1000,
            "current_spend": 500,
            "usage_percent": 50.0,
        }

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.get_budget",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert result["name"] == "my-budget"
        assert result["usage_percent"] == 50.0


# =============================================================================
# CostRecommendationsOptions Tests
# =============================================================================


class TestCostRecommendationsOptions:
    """Tests for CostRecommendationsOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = CostRecommendationsOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.category == "Cost"

    def test_all_categories(self):
        """Test valid category values."""
        for cat in [
            "Cost",
            "Security",
            "Performance",
            "HighAvailability",
            "OperationalExcellence",
            "",
        ]:
            options = CostRecommendationsOptions(subscription="my-sub", category=cat)
            assert options.category == cat


# =============================================================================
# CostRecommendationsTool Tests
# =============================================================================


class TestCostRecommendationsTool:
    """Tests for CostRecommendationsTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostRecommendationsTool()
        assert tool.name == "cost_recommendations"
        assert "advisor" in tool.description.lower() or "recommendation" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostRecommendationsTool()
        options = CostRecommendationsOptions(subscription="my-sub")

        mock_result = [
            {
                "name": "resize-vm",
                "category": "Cost",
                "impact": "High",
                "annual_savings": 500.0,
            },
        ]

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.list_cost_recommendations",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 1
        assert result[0]["annual_savings"] == 500.0


# =============================================================================
# CostExportsListOptions Tests
# =============================================================================


class TestCostExportsListOptions:
    """Tests for CostExportsListOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = CostExportsListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""


# =============================================================================
# CostExportsListTool Tests
# =============================================================================


class TestCostExportsListTool:
    """Tests for CostExportsListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CostExportsListTool()
        assert tool.name == "cost_exports_list"
        assert "export" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = CostExportsListTool()
        options = CostExportsListOptions(subscription="my-sub")

        mock_result = [
            {
                "name": "daily-export",
                "schedule_recurrence": "Daily",
                "destination_container": "cost-data",
            },
        ]

        with patch(
            "azure_mcp.tools.cost.service.CostManagementService.list_exports",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 1
        assert result[0]["name"] == "daily-export"


# =============================================================================
# CostManagementService Tests
# =============================================================================


class TestCostManagementService:
    """Tests for CostManagementService."""

    @pytest.mark.asyncio
    async def test_build_scope_subscription_only(self):
        """Test scope building for subscription only."""
        from azure_mcp.tools.cost.service import CostManagementService

        service = CostManagementService()
        scope = service._build_scope("12345-6789", "")
        assert scope == "/subscriptions/12345-6789"

    @pytest.mark.asyncio
    async def test_build_scope_with_resource_group(self):
        """Test scope building with resource group."""
        from azure_mcp.tools.cost.service import CostManagementService

        service = CostManagementService()
        scope = service._build_scope("12345-6789", "my-rg")
        assert scope == "/subscriptions/12345-6789/resourceGroups/my-rg"

    @pytest.mark.asyncio
    async def test_query_costs(self):
        """Test query_costs calls Azure SDK correctly."""
        from azure_mcp.tools.cost.service import CostManagementService

        service = CostManagementService()

        # Mock the Azure SDK client
        mock_column = MagicMock()
        mock_column.name = "Cost"
        mock_column.type = "Number"

        mock_result = MagicMock()
        mock_result.columns = [mock_column]
        mock_result.rows = [[100.0]]
        mock_result.next_link = None

        mock_client = MagicMock()
        mock_client.query.usage.return_value = mock_result

        with (
            patch(
                "azure_mcp.tools.cost.service.CostManagementService.resolve_subscription",
                new_callable=AsyncMock,
                return_value="12345-6789",
            ),
            patch(
                "azure_mcp.tools.cost.service.CostManagementService.get_credential",
                return_value=MagicMock(),
            ),
            patch(
                "azure.mgmt.costmanagement.CostManagementClient",
                return_value=mock_client,
            ),
        ):
            result = await service.query_costs(
                subscription="my-sub",
                timeframe="MonthToDate",
            )

        assert result["columns"][0]["name"] == "Cost"
        assert result["rows"][0][0] == 100.0
        mock_client.query.usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_budgets(self):
        """Test list_budgets calls Azure SDK correctly."""
        from datetime import datetime
        from azure_mcp.tools.cost.service import CostManagementService

        service = CostManagementService()

        # Mock budget object
        mock_budget = MagicMock()
        mock_budget.name = "monthly-budget"
        mock_budget.id = "/subscriptions/123/budgets/monthly-budget"
        mock_budget.amount = 1000
        mock_budget.time_grain = "Monthly"
        mock_budget.category = "Cost"
        mock_budget.current_spend = MagicMock(amount=500, unit="USD")
        mock_budget.time_period = MagicMock()
        mock_budget.time_period.start_date = datetime(2026, 1, 1)
        mock_budget.time_period.end_date = datetime(2026, 12, 31)

        mock_client = MagicMock()
        mock_client.budgets.list.return_value = [mock_budget]

        with (
            patch(
                "azure_mcp.tools.cost.service.CostManagementService.resolve_subscription",
                new_callable=AsyncMock,
                return_value="12345-6789",
            ),
            patch(
                "azure_mcp.tools.cost.service.CostManagementService.get_credential",
                return_value=MagicMock(),
            ),
            patch(
                "azure.mgmt.consumption.ConsumptionManagementClient",
                return_value=mock_client,
            ),
        ):
            result = await service.list_budgets(subscription="my-sub")

        assert len(result) == 1
        assert result[0]["name"] == "monthly-budget"
        assert result[0]["amount"] == 1000
        assert result[0]["current_spend"] == 500

    @pytest.mark.asyncio
    async def test_list_cost_recommendations(self):
        """Test list_cost_recommendations calls Azure SDK correctly."""
        from azure_mcp.tools.cost.service import CostManagementService

        service = CostManagementService()

        # Mock recommendation object
        mock_rec = MagicMock()
        mock_rec.id = "/subscriptions/123/recommendations/1"
        mock_rec.name = "resize-vm"
        mock_rec.category = "Cost"
        mock_rec.impact = "High"
        mock_rec.impacted_field = "VirtualMachine"
        mock_rec.impacted_value = "vm-1"
        mock_rec.short_description = MagicMock(problem="VM underutilized", solution="Resize to B2s")
        mock_rec.potential_benefits = "Save $500/year"
        mock_rec.extended_properties = {"annualSavingsAmount": "500", "savingsCurrency": "USD"}
        mock_rec.resource_metadata = MagicMock(
            resource_id="/subscriptions/123/vm/vm-1", source="Azure"
        )
        mock_rec.last_updated = None

        mock_client = MagicMock()
        mock_client.recommendations.list.return_value = [mock_rec]

        with (
            patch(
                "azure_mcp.tools.cost.service.CostManagementService.resolve_subscription",
                new_callable=AsyncMock,
                return_value="12345-6789",
            ),
            patch(
                "azure_mcp.tools.cost.service.CostManagementService.get_credential",
                return_value=MagicMock(),
            ),
            patch.dict(
                "sys.modules",
                {
                    "azure.mgmt.advisor": MagicMock(
                        AdvisorManagementClient=MagicMock(return_value=mock_client)
                    )
                },
            ),
        ):
            result = await service.list_cost_recommendations(subscription="my-sub")

        assert len(result) == 1
        assert result[0]["name"] == "resize-vm"
        assert result[0]["annual_savings"] == 500.0
