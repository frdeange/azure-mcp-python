"""Azure Monitor log query tools."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.monitor.service import MonitorService


class LogsQueryOptions(BaseModel):
    """Options for querying Log Analytics workspace."""

    workspace_id: str = Field(
        ...,
        description="The Log Analytics workspace ID (GUID). Use monitor_workspace_list to find workspace IDs.",
    )
    query: str = Field(
        ...,
        description="The KQL (Kusto Query Language) query to execute.",
    )
    timespan_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Time range in hours to query (1-720, default 24).",
    )
    include_statistics: bool = Field(
        default=False,
        description="Whether to include query execution statistics.",
    )


class LogsQueryResourceOptions(BaseModel):
    """Options for querying logs directly from a resource."""

    resource_id: str = Field(
        ...,
        description="The full Azure resource ID to query logs from.",
    )
    query: str = Field(
        ...,
        description="The KQL (Kusto Query Language) query to execute.",
    )
    timespan_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Time range in hours to query (1-720, default 24).",
    )
    include_statistics: bool = Field(
        default=False,
        description="Whether to include query execution statistics.",
    )


class LogsBatchQueryOptions(BaseModel):
    """Options for batch log queries."""

    workspace_id: str = Field(
        ...,
        description="The Log Analytics workspace ID (GUID).",
    )
    queries_json: str = Field(
        ...,
        description=(
            "JSON array of query objects. Each object must have 'id' (string identifier) "
            "and 'query' (KQL string). Example: "
            '[{"id":"q1","query":"AzureActivity | take 10"},{"id":"q2","query":"Heartbeat | take 5"}]'
        ),
    )
    timespan_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Default time range in hours for all queries.",
    )


@register_tool("monitor", "logs")
class MonitorLogsQueryTool(AzureTool):
    """Query Log Analytics workspace using KQL."""

    @property
    def name(self) -> str:
        return "monitor_logs_query"

    @property
    def description(self) -> str:
        return (
            "Execute a KQL (Kusto Query Language) query against a Log Analytics workspace. "
            "Use this for analyzing telemetry, investigating issues, and searching logs. "
            "Examples: query container logs, application traces, security events, performance data. "
            "First use monitor_workspace_list to find workspace IDs."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return LogsQueryOptions

    async def execute(self, options: LogsQueryOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        return await service.query_logs(
            workspace_id=options.workspace_id,
            query=options.query,
            timespan=timedelta(hours=options.timespan_hours),
            include_statistics=options.include_statistics,
        )


@register_tool("monitor", "logs")
class MonitorLogsQueryResourceTool(AzureTool):
    """Query logs directly from an Azure resource."""

    @property
    def name(self) -> str:
        return "monitor_logs_query_resource"

    @property
    def description(self) -> str:
        return (
            "Execute a KQL query directly against an Azure resource without needing the workspace ID. "
            "Simpler when you know the resource ID but not the Log Analytics workspace. "
            "Supports any resource that sends logs to Azure Monitor."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return LogsQueryResourceOptions

    async def execute(self, options: LogsQueryResourceOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        return await service.query_logs_resource(
            resource_id=options.resource_id,
            query=options.query,
            timespan=timedelta(hours=options.timespan_hours),
            include_statistics=options.include_statistics,
        )


@register_tool("monitor", "logs")
class MonitorLogsBatchQueryTool(AzureTool):
    """Execute multiple KQL queries in a single batch request."""

    @property
    def name(self) -> str:
        return "monitor_logs_batch_query"

    @property
    def description(self) -> str:
        return (
            "Execute multiple KQL queries against a Log Analytics workspace in a single batch request. "
            "More efficient than making multiple individual queries. "
            "Each query should have an 'id' for identification and 'query' with the KQL."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return LogsBatchQueryOptions

    async def execute(self, options: LogsBatchQueryOptions) -> Any:  # type: ignore[override]
        import json
        service = MonitorService()
        # Parse JSON string to list of queries
        queries = json.loads(options.queries_json)
        return await service.query_logs_batch(
            workspace_id=options.workspace_id,
            queries=queries,
            timespan=timedelta(hours=options.timespan_hours),
        )
