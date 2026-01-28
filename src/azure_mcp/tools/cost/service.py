"""Cost Management service for Azure operations.

Provides methods for querying costs, forecasts, budgets, and recommendations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from azure_mcp.core.base import AzureService


class CostManagementService(AzureService):
    """Service for Azure Cost Management operations."""

    def _build_scope(
        self,
        subscription_id: str,
        resource_group: str = "",
    ) -> str:
        """Build scope string for Cost Management API."""
        if resource_group:
            return f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        return f"/subscriptions/{subscription_id}"

    async def query_costs(
        self,
        subscription: str,
        resource_group: str = "",
        timeframe: str = "MonthToDate",
        granularity: str = "None",
        group_by: str = "",
        filter_expression: str = "",
        metric_type: str = "ActualCost",
    ) -> dict[str, Any]:
        """
        Query cost data using Cost Management API.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            timeframe: Time period (MonthToDate, BillingMonthToDate, TheLastMonth, etc.)
            granularity: Data granularity (None, Daily, Monthly).
            group_by: Dimension to group by (ResourceGroup, ResourceType, ServiceName, etc.)
            filter_expression: Filter expression for costs.
            metric_type: Type of cost metric (ActualCost, AmortizedCost).

        Returns:
            Query results with columns and rows.
        """
        from azure.mgmt.costmanagement import CostManagementClient
        from azure.mgmt.costmanagement.models import (
            GranularityType,
            QueryAggregation,
            QueryDataset,
            QueryDefinition,
            QueryGrouping,
            TimeframeType,
        )

        sub_id = await self.resolve_subscription(subscription)
        scope = self._build_scope(sub_id, resource_group)
        credential = self.get_credential()

        client = CostManagementClient(credential)

        # Build aggregation
        aggregation = {
            "totalCost": QueryAggregation(name="Cost", function="Sum"),
            "totalCostUSD": QueryAggregation(name="CostUSD", function="Sum"),
        }

        # Build grouping if specified
        grouping = None
        if group_by:
            grouping = [QueryGrouping(type="Dimension", name=group_by)]

        # Build dataset
        dataset = QueryDataset(
            granularity=GranularityType(granularity) if granularity != "None" else None,
            aggregation=aggregation,
            grouping=grouping,
        )

        # Build query definition
        query = QueryDefinition(
            type=metric_type,
            timeframe=TimeframeType(timeframe),
            dataset=dataset,
        )

        result = client.query.usage(scope=scope, parameters=query)

        # Transform result to dict
        columns = [{"name": col.name, "type": col.type} for col in result.columns]
        rows = list(result.rows) if result.rows else []

        return {
            "columns": columns,
            "rows": rows,
            "next_link": result.next_link,
            "scope": scope,
            "timeframe": timeframe,
            "granularity": granularity,
        }

    async def query_costs_by_resource(
        self,
        subscription: str,
        resource_group: str = "",
        timeframe: str = "MonthToDate",
        top: int = 20,
        metric_type: str = "ActualCost",
    ) -> list[dict[str, Any]]:
        """
        Get cost breakdown by individual resources.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            timeframe: Time period for costs.
            top: Maximum number of resources to return.
            metric_type: Type of cost metric.

        Returns:
            List of resources with their costs.
        """
        result = await self.query_costs(
            subscription=subscription,
            resource_group=resource_group,
            timeframe=timeframe,
            granularity="None",
            group_by="ResourceId",
            metric_type=metric_type,
        )

        # Transform rows to resource cost objects
        resources = []
        rows = result.get("rows", [])
        columns = result.get("columns", [])

        # Find column indices
        cost_idx = next((i for i, c in enumerate(columns) if c["name"] == "Cost"), 0)
        cost_usd_idx = next((i for i, c in enumerate(columns) if c["name"] == "CostUSD"), 1)
        resource_id_idx = next((i for i, c in enumerate(columns) if c["name"] == "ResourceId"), 2)

        for row in rows:
            if len(row) > max(cost_idx, cost_usd_idx, resource_id_idx):
                resource_id = row[resource_id_idx] if resource_id_idx < len(row) else ""
                resources.append(
                    {
                        "resource_id": resource_id,
                        "resource_name": resource_id.split("/")[-1] if resource_id else "",
                        "cost": row[cost_idx] if cost_idx < len(row) else 0,
                        "cost_usd": row[cost_usd_idx] if cost_usd_idx < len(row) else 0,
                        "currency": "USD",
                    }
                )

        # Sort by cost descending and limit
        resources.sort(key=lambda x: x.get("cost", 0), reverse=True)
        return resources[:top]

    async def get_forecast(
        self,
        subscription: str,
        resource_group: str = "",
        granularity: str = "Daily",
        include_actual_cost: bool = True,
        include_fresh_partial_cost: bool = True,
        forecast_days: int = 30,
    ) -> dict[str, Any]:
        """
        Get cost forecast for a subscription.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            granularity: Forecast granularity (Daily, Monthly).
            include_actual_cost: Include actual costs in response.
            include_fresh_partial_cost: Include partial period costs.
            forecast_days: Number of days to forecast.

        Returns:
            Forecast data with columns and rows.
        """
        from azure.mgmt.costmanagement import CostManagementClient
        from azure.mgmt.costmanagement.models import (
            ForecastAggregation,
            ForecastDataset,
            ForecastDefinition,
            ForecastTimePeriod,
            GranularityType,
        )

        sub_id = await self.resolve_subscription(subscription)
        scope = self._build_scope(sub_id, resource_group)
        credential = self.get_credential()

        client = CostManagementClient(credential)

        # Calculate time period
        now = datetime.now(UTC)
        end_date = now + timedelta(days=forecast_days)

        # Build aggregation
        aggregation = {
            "totalCost": ForecastAggregation(name="Cost", function="Sum"),
        }

        # Build dataset
        dataset = ForecastDataset(
            granularity=GranularityType(granularity),
            aggregation=aggregation,
        )

        # Build forecast definition
        forecast = ForecastDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=ForecastTimePeriod(
                from_property=now,
                to=end_date,
            ),
            dataset=dataset,
            include_actual_cost=include_actual_cost,
            include_fresh_partial_cost=include_fresh_partial_cost,
        )

        result = client.forecast.usage(scope=scope, parameters=forecast)

        # Transform result
        columns = [{"name": col.name, "type": col.type} for col in result.columns]
        rows = list(result.rows) if result.rows else []

        return {
            "columns": columns,
            "rows": rows,
            "scope": scope,
            "forecast_days": forecast_days,
            "granularity": granularity,
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
        }

    async def list_budgets(
        self,
        subscription: str,
        resource_group: str = "",
    ) -> list[dict[str, Any]]:
        """
        List budgets for a subscription or resource group.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group scope.

        Returns:
            List of budget summaries.
        """
        from azure.mgmt.consumption import ConsumptionManagementClient

        sub_id = await self.resolve_subscription(subscription)
        scope = self._build_scope(sub_id, resource_group)
        credential = self.get_credential()

        client = ConsumptionManagementClient(credential, sub_id)

        budgets = []
        for budget in client.budgets.list(scope=scope):
            # Handle optional time_period
            time_start = None
            time_end = None
            if budget.time_period:
                if budget.time_period.start_date:
                    time_start = budget.time_period.start_date.isoformat()
                if budget.time_period.end_date:
                    time_end = budget.time_period.end_date.isoformat()

            budgets.append(
                {
                    "name": budget.name,
                    "id": budget.id,
                    "amount": budget.amount,
                    "time_grain": budget.time_grain,
                    "category": budget.category,
                    "current_spend": budget.current_spend.amount if budget.current_spend else None,
                    "current_spend_unit": budget.current_spend.unit
                    if budget.current_spend
                    else None,
                    "time_period_start": time_start,
                    "time_period_end": time_end,
                }
            )

        return budgets

    async def get_budget(
        self,
        subscription: str,
        budget_name: str,
        resource_group: str = "",
    ) -> dict[str, Any]:
        """
        Get detailed budget information.

        Args:
            subscription: Subscription ID or name.
            budget_name: Name of the budget.
            resource_group: Optional resource group scope.

        Returns:
            Detailed budget information.
        """
        from azure.mgmt.consumption import ConsumptionManagementClient

        sub_id = await self.resolve_subscription(subscription)
        scope = self._build_scope(sub_id, resource_group)
        credential = self.get_credential()

        client = ConsumptionManagementClient(credential, sub_id)

        budget = client.budgets.get(scope=scope, budget_name=budget_name)

        # Extract notifications
        notifications = []
        if budget.notifications:
            for name, notif in budget.notifications.items():
                notifications.append(
                    {
                        "name": name,
                        "enabled": notif.enabled,
                        "operator": notif.operator,
                        "threshold": notif.threshold,
                        "contact_emails": list(notif.contact_emails)
                        if notif.contact_emails
                        else [],
                        "threshold_type": notif.threshold_type,
                    }
                )

        # Calculate usage percentage
        current = budget.current_spend.amount if budget.current_spend else 0
        amount = budget.amount or 1
        usage_percent = (current / amount) * 100

        return {
            "name": budget.name,
            "id": budget.id,
            "amount": budget.amount,
            "time_grain": budget.time_grain,
            "category": budget.category,
            "current_spend": current,
            "current_spend_unit": budget.current_spend.unit if budget.current_spend else None,
            "usage_percent": round(usage_percent, 2),
            "time_period_start": budget.time_period.start_date.isoformat()
            if budget.time_period
            else None,
            "time_period_end": budget.time_period.end_date.isoformat()
            if budget.time_period
            else None,
            "notifications": notifications,
            "filter": str(budget.filter) if budget.filter else None,
        }

    async def list_cost_recommendations(
        self,
        subscription: str,
        category: str = "",
    ) -> list[dict[str, Any]]:
        """
        Get Azure Advisor cost recommendations.

        Args:
            subscription: Subscription ID or name.
            category: Filter by category (Cost, Security, Performance, etc.)

        Returns:
            List of cost optimization recommendations.
        """
        from azure.mgmt.advisor import AdvisorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        client = AdvisorManagementClient(credential, sub_id)

        # Build filter
        filter_str = "Category eq 'Cost'" if not category else f"Category eq '{category}'"

        recommendations = []
        for rec in client.recommendations.list(filter=filter_str):
            # Extract savings if available
            extended_props = rec.extended_properties or {}
            annual_savings = extended_props.get("annualSavingsAmount")
            savings_currency = extended_props.get("savingsCurrency", "USD")

            recommendations.append(
                {
                    "id": rec.id,
                    "name": rec.name,
                    "category": rec.category,
                    "impact": rec.impact,
                    "impacted_field": rec.impacted_field,
                    "impacted_value": rec.impacted_value,
                    "short_description": rec.short_description.problem
                    if rec.short_description
                    else None,
                    "solution": rec.short_description.solution if rec.short_description else None,
                    "potential_benefits": getattr(rec, "potential_benefits", None),
                    "annual_savings": float(annual_savings) if annual_savings else None,
                    "savings_currency": savings_currency,
                    "resource_metadata": {
                        "resource_id": rec.resource_metadata.resource_id
                        if rec.resource_metadata
                        else None,
                        "source": rec.resource_metadata.source if rec.resource_metadata else None,
                    }
                    if rec.resource_metadata
                    else None,
                    "last_updated": rec.last_updated.isoformat() if rec.last_updated else None,
                }
            )

        return recommendations

    async def list_exports(
        self,
        subscription: str,
        resource_group: str = "",
    ) -> list[dict[str, Any]]:
        """
        List configured cost exports.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group scope.

        Returns:
            List of cost export configurations.
        """
        from azure.mgmt.costmanagement import CostManagementClient

        sub_id = await self.resolve_subscription(subscription)
        scope = self._build_scope(sub_id, resource_group)
        credential = self.get_credential()

        client = CostManagementClient(credential)

        result = client.exports.list(scope=scope)
        exports = []
        for export in result.value or []:
            # Get delivery info
            delivery = export.delivery_info
            destination = delivery.destination if delivery else None

            exports.append(
                {
                    "name": export.name,
                    "id": export.id,
                    "format": export.format,
                    "definition_type": export.definition.type if export.definition else None,
                    "definition_timeframe": export.definition.timeframe
                    if export.definition
                    else None,
                    "schedule_status": export.schedule.status if export.schedule else None,
                    "schedule_recurrence": export.schedule.recurrence if export.schedule else None,
                    "next_run_time": export.next_run_time_estimate.isoformat()
                    if export.next_run_time_estimate
                    else None,
                    "destination_container": destination.container if destination else None,
                    "destination_root_folder": destination.root_folder_path
                    if destination
                    else None,
                    "destination_resource_id": destination.resource_id if destination else None,
                }
            )

        return exports
