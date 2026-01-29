"""Application Insights service implementation.

Uses Azure Monitor Query SDK for querying Application Insights data.
Application Insights queries use the same LogsQueryClient but target
the App Insights resource directly via query_resource().
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import structlog
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus

from azure_mcp.core.auth import CredentialProvider
from azure_mcp.core.base import AzureService
from azure_mcp.core.cache import cache

logger = structlog.get_logger()


class AppInsightsService(AzureService):
    """Service for Application Insights operations.

    Uses LogsQueryClient.query_resource() to query Application Insights
    resources directly, which is the recommended approach for App Insights.
    """

    def _get_logs_client(self) -> LogsQueryClient:
        """Get a LogsQueryClient instance."""
        credential = CredentialProvider.get_credential()
        return LogsQueryClient(credential)

    async def list_app_insights(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """List Application Insights resources using Resource Graph.

        Args:
            subscription: Subscription ID or display name.
            resource_group: Optional resource group filter.
            top: Maximum number of results.

        Returns:
            List of Application Insights resources with key properties.
        """
        sub_id = await self.resolve_subscription(subscription)

        filters = ["type =~ 'microsoft.insights/components'"]
        if resource_group:
            filters.append(f"resourceGroup =~ '{resource_group}'")

        query = f"""
        Resources
        | where {" and ".join(filters)}
        | project
            id,
            name,
            resourceGroup,
            location,
            subscriptionId,
            appId = properties.AppId,
            instrumentationKey = properties.InstrumentationKey,
            connectionString = properties.ConnectionString,
            applicationType = properties.Application_Type,
            ingestionMode = properties.IngestionMode,
            workspaceResourceId = properties.WorkspaceResourceId,
            retentionInDays = properties.RetentionInDays,
            publicNetworkAccess = properties.publicNetworkAccessForIngestion,
            provisioningState = properties.provisioningState,
            createdDate = properties.CreationDate,
            tags
        | order by name asc
        | take {top}
        """

        return await self.run_resource_graph_query(query, [sub_id])

    async def get_app_insights(
        self,
        subscription: str,
        resource_group: str,
        name: str,
    ) -> dict[str, Any]:
        """Get a specific Application Insights resource.

        Args:
            subscription: Subscription ID or display name.
            resource_group: Resource group containing the resource.
            name: Application Insights resource name.

        Returns:
            Application Insights resource details.

        Raises:
            ResourceNotFoundError: If the resource doesn't exist.
        """
        sub_id = await self.resolve_subscription(subscription)

        query = f"""
        Resources
        | where type =~ 'microsoft.insights/components'
        | where subscriptionId =~ '{sub_id}'
        | where resourceGroup =~ '{resource_group}'
        | where name =~ '{name}'
        | project
            id,
            name,
            resourceGroup,
            location,
            subscriptionId,
            appId = properties.AppId,
            instrumentationKey = properties.InstrumentationKey,
            connectionString = properties.ConnectionString,
            applicationType = properties.Application_Type,
            ingestionMode = properties.IngestionMode,
            workspaceResourceId = properties.WorkspaceResourceId,
            retentionInDays = properties.RetentionInDays,
            publicNetworkAccess = properties.publicNetworkAccessForIngestion,
            provisioningState = properties.provisioningState,
            createdDate = properties.CreationDate,
            tags
        """

        results = await self.run_resource_graph_query(query, [sub_id])
        if not results:
            from azure_mcp.core.errors import ResourceNotFoundError

            raise ResourceNotFoundError(
                f"Application Insights '{name}' not found in resource group '{resource_group}'"
            )

        return results[0]

    async def query(
        self,
        resource_id: str,
        query: str,
        timespan: str = "P1D",
        top: int = 100,
    ) -> dict[str, Any]:
        """Run a custom KQL query against Application Insights.

        Args:
            resource_id: Full resource ID of the Application Insights resource.
            query: KQL query to execute.
            timespan: ISO 8601 duration (e.g., "PT1H", "P1D", "P7D").
            top: Maximum rows to return (appended as | take N).

        Returns:
            Query results with columns and rows.
        """
        client = self._get_logs_client()

        # Append top limit if not already in query
        effective_query = query
        if "| take " not in query.lower() and "| limit " not in query.lower():
            effective_query = f"{query}\n| take {top}"

        timespan_delta = self._parse_iso_duration(timespan)

        try:
            response = await asyncio.to_thread(
                client.query_resource,
                resource_id,
                effective_query,
                timespan=timespan_delta,
            )

            if response.status == LogsQueryStatus.SUCCESS:
                return self._format_query_response(response)
            elif response.status == LogsQueryStatus.PARTIAL:
                return {
                    "status": "partial",
                    "error": str(response.partial_error),
                    **self._format_query_response(response),
                }
            else:
                return {
                    "status": "failed",
                    "error": "Query failed with no results",
                }

        except HttpResponseError as e:
            logger.error("App Insights query failed", error=str(e))
            raise

    async def query_traces(
        self,
        resource_id: str,
        timespan: str = "P1D",
        severity_level: str = "",
        message_filter: str = "",
        top: int = 100,
    ) -> dict[str, Any]:
        """Query application traces/logs.

        Args:
            resource_id: Full resource ID of the App Insights resource.
            timespan: ISO 8601 duration.
            severity_level: Filter by level (Verbose, Information, Warning, Error, Critical).
            message_filter: Filter message contains this text.
            top: Maximum rows.

        Returns:
            Trace records.
        """
        filters = []
        if severity_level:
            # Map string to numeric level if needed
            level_map = {
                "verbose": 0,
                "information": 1,
                "warning": 2,
                "error": 3,
                "critical": 4,
            }
            level_num = level_map.get(severity_level.lower())
            if level_num is not None:
                filters.append(f"severityLevel == {level_num}")
            else:
                filters.append(f"severityLevel == {severity_level}")

        if message_filter:
            filters.append(f"message contains '{message_filter}'")

        where_clause = f"| where {' and '.join(filters)}" if filters else ""

        query = f"""
        traces
        {where_clause}
        | project
            timestamp,
            message,
            severityLevel,
            customDimensions,
            operation_Id,
            operation_Name,
            cloud_RoleName,
            cloud_RoleInstance,
            appId,
            itemId
        | order by timestamp desc
        | take {top}
        """

        return await self.query(resource_id, query, timespan, top)

    async def query_exceptions(
        self,
        resource_id: str,
        timespan: str = "P1D",
        exception_type: str = "",
        problem_id: str = "",
        top: int = 100,
    ) -> dict[str, Any]:
        """Query exception telemetry.

        Args:
            resource_id: Full resource ID of the App Insights resource.
            timespan: ISO 8601 duration.
            exception_type: Filter by exception type name.
            problem_id: Filter by problem ID.
            top: Maximum rows.

        Returns:
            Exception records.
        """
        filters = []
        if exception_type:
            filters.append(f"type contains '{exception_type}'")
        if problem_id:
            filters.append(f"problemId == '{problem_id}'")

        where_clause = f"| where {' and '.join(filters)}" if filters else ""

        query = f"""
        exceptions
        {where_clause}
        | project
            timestamp,
            type,
            message,
            outerMessage,
            innermostMessage,
            problemId,
            handledAt,
            severityLevel,
            details,
            operation_Id,
            operation_Name,
            cloud_RoleName,
            cloud_RoleInstance,
            appId,
            itemId
        | order by timestamp desc
        | take {top}
        """

        return await self.query(resource_id, query, timespan, top)

    async def query_requests(
        self,
        resource_id: str,
        timespan: str = "P1D",
        url_filter: str = "",
        result_code: str = "",
        success: str = "",
        min_duration_ms: int = 0,
        top: int = 100,
    ) -> dict[str, Any]:
        """Query HTTP request telemetry.

        Args:
            resource_id: Full resource ID of the App Insights resource.
            timespan: ISO 8601 duration.
            url_filter: Filter URLs containing this text.
            result_code: Filter by HTTP status code.
            success: Filter by success ("true" or "false").
            min_duration_ms: Minimum duration in milliseconds.
            top: Maximum rows.

        Returns:
            Request records.
        """
        filters = []
        if url_filter:
            filters.append(f"url contains '{url_filter}'")
        if result_code:
            filters.append(f"resultCode == '{result_code}'")
        if success:
            filters.append(f"success == {success.lower()}")
        if min_duration_ms > 0:
            filters.append(f"duration > {min_duration_ms}")

        where_clause = f"| where {' and '.join(filters)}" if filters else ""

        query = f"""
        requests
        {where_clause}
        | project
            timestamp,
            name,
            url,
            resultCode,
            success,
            duration,
            performanceBucket,
            source,
            operation_Id,
            operation_Name,
            cloud_RoleName,
            cloud_RoleInstance,
            appId,
            itemId
        | order by timestamp desc
        | take {top}
        """

        return await self.query(resource_id, query, timespan, top)

    async def query_dependencies(
        self,
        resource_id: str,
        timespan: str = "P1D",
        dependency_type: str = "",
        target: str = "",
        success: str = "",
        min_duration_ms: int = 0,
        top: int = 100,
    ) -> dict[str, Any]:
        """Query dependency call telemetry.

        Args:
            resource_id: Full resource ID of the App Insights resource.
            timespan: ISO 8601 duration.
            dependency_type: Filter by type (e.g., "SQL", "HTTP", "Azure blob").
            target: Filter target contains this text.
            success: Filter by success ("true" or "false").
            min_duration_ms: Minimum duration in milliseconds.
            top: Maximum rows.

        Returns:
            Dependency records.
        """
        filters = []
        if dependency_type:
            filters.append(f"type == '{dependency_type}'")
        if target:
            filters.append(f"target contains '{target}'")
        if success:
            filters.append(f"success == {success.lower()}")
        if min_duration_ms > 0:
            filters.append(f"duration > {min_duration_ms}")

        where_clause = f"| where {' and '.join(filters)}" if filters else ""

        query = f"""
        dependencies
        {where_clause}
        | project
            timestamp,
            name,
            type,
            target,
            data,
            resultCode,
            success,
            duration,
            performanceBucket,
            operation_Id,
            operation_Name,
            cloud_RoleName,
            cloud_RoleInstance,
            appId,
            itemId
        | order by timestamp desc
        | take {top}
        """

        return await self.query(resource_id, query, timespan, top)

    async def query_events(
        self,
        resource_id: str,
        timespan: str = "P1D",
        event_name: str = "",
        top: int = 100,
    ) -> dict[str, Any]:
        """Query custom events.

        Args:
            resource_id: Full resource ID of the App Insights resource.
            timespan: ISO 8601 duration.
            event_name: Filter by event name.
            top: Maximum rows.

        Returns:
            Custom event records.
        """
        filters = []
        if event_name:
            filters.append(f"name == '{event_name}'")

        where_clause = f"| where {' and '.join(filters)}" if filters else ""

        query = f"""
        customEvents
        {where_clause}
        | project
            timestamp,
            name,
            customDimensions,
            customMeasurements,
            operation_Id,
            operation_Name,
            cloud_RoleName,
            cloud_RoleInstance,
            appId,
            itemId
        | order by timestamp desc
        | take {top}
        """

        return await self.query(resource_id, query, timespan, top)

    def _parse_iso_duration(self, duration: str) -> timedelta:
        """Parse ISO 8601 duration to timedelta.

        Supports:
        - PT1H (1 hour)
        - PT30M (30 minutes)
        - P1D (1 day)
        - P7D (7 days)
        - P1M (30 days - approximate)
        """
        import re

        duration = duration.upper()

        # Simple patterns
        patterns = {
            r"^PT(\d+)M$": lambda m: timedelta(minutes=int(m.group(1))),
            r"^PT(\d+)H$": lambda m: timedelta(hours=int(m.group(1))),
            r"^P(\d+)D$": lambda m: timedelta(days=int(m.group(1))),
            r"^P(\d+)W$": lambda m: timedelta(weeks=int(m.group(1))),
            r"^P(\d+)M$": lambda m: timedelta(days=int(m.group(1)) * 30),
        }

        for pattern, handler in patterns.items():
            match = re.match(pattern, duration)
            if match:
                return handler(match)

        # Default to 1 day
        return timedelta(days=1)

    def _format_query_response(self, response: Any) -> dict[str, Any]:
        """Format query response to dict."""
        tables = []

        for table in response.tables:
            columns = [col.name for col in table.columns]
            rows = []

            for row in table.rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert datetime to string for JSON serialization
                    if hasattr(value, "isoformat"):
                        value = value.isoformat()
                    row_dict[col] = value
                rows.append(row_dict)

            tables.append(
                {
                    "name": table.name,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                }
            )

        return {
            "status": "success",
            "tables": tables,
            "total_rows": sum(t["row_count"] for t in tables),
        }
