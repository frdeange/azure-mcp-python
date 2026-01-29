"""Azure Monitor metrics query tools."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.monitor.service import MonitorService


class MetricsQueryOptions(BaseModel):
    """Options for querying resource metrics."""

    resource_id: str = Field(
        ...,
        description="The full Azure resource ID to query metrics from.",
    )
    metric_names: list[str] = Field(
        ...,
        description="List of metric names to query (e.g., ['Percentage CPU', 'Network In Total']).",
    )
    timespan_hours: int = Field(
        default=1,
        ge=1,
        le=720,
        description="Time range in hours (1-720, default 1).",
    )
    interval: str = Field(
        default="PT1M",
        description="Aggregation interval in ISO 8601 format (PT1M, PT5M, PT15M, PT30M, PT1H, PT6H, PT12H, P1D).",
    )
    aggregations: list[str] = Field(
        default_factory=lambda: ["Average"],
        description="Aggregation types: Average, Total, Maximum, Minimum, Count.",
    )


class MetricDefinitionsListOptions(BaseModel):
    """Options for listing metric definitions."""

    resource_id: str = Field(
        ...,
        description="The full Azure resource ID to list available metrics for.",
    )


class MetricBaselinesGetOptions(BaseModel):
    """Options for getting metric baselines."""

    resource_id: str = Field(
        ...,
        description="The full Azure resource ID.",
    )
    metric_names: list[str] = Field(
        ...,
        description="List of metric names to get baselines for.",
    )
    timespan_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Time range in hours for baseline calculation.",
    )
    interval: str = Field(
        default="PT1H",
        description="Aggregation interval in ISO 8601 format.",
    )


@register_tool("monitor", "metrics")
class MonitorMetricsQueryTool(AzureTool):
    """Query metrics for an Azure resource."""

    @property
    def name(self) -> str:
        return "monitor_metrics_query"

    @property
    def description(self) -> str:
        return (
            "Query performance metrics for any Azure resource. "
            "Returns time-series data for metrics like CPU usage, memory, network I/O, "
            "request count, latency, etc. Use monitor_metric_definitions_list first "
            "to discover available metrics for a resource."
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
        return MetricsQueryOptions

    async def execute(self, options: MetricsQueryOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.query_metrics(
                resource_id=options.resource_id,
                metric_names=options.metric_names,
                timespan=timedelta(hours=options.timespan_hours),
                interval=options.interval,
                aggregations=options.aggregations,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Metrics Query") from e


@register_tool("monitor", "metrics")
class MonitorMetricDefinitionsListTool(AzureTool):
    """List available metrics for a resource."""

    @property
    def name(self) -> str:
        return "monitor_metric_definitions_list"

    @property
    def description(self) -> str:
        return (
            "List all available metric definitions for an Azure resource. "
            "Shows metric names, units, aggregation types, and data retention. "
            "Use this to discover what metrics can be queried with monitor_metrics_query."
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
        return MetricDefinitionsListOptions

    async def execute(self, options: MetricDefinitionsListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_metric_definitions(
                resource_id=options.resource_id,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Metric Definitions") from e


@register_tool("monitor", "metrics")
class MonitorMetricBaselinesGetTool(AzureTool):
    """Get metric baselines for anomaly detection."""

    @property
    def name(self) -> str:
        return "monitor_metric_baselines_get"

    @property
    def description(self) -> str:
        return (
            "Get metric baselines for a resource, useful for anomaly detection. "
            "Returns expected low and high thresholds based on historical patterns. "
            "Helps identify when metrics deviate from normal behavior."
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
        return MetricBaselinesGetOptions

    async def execute(self, options: MetricBaselinesGetOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.get_metric_baselines(
                resource_id=options.resource_id,
                metric_names=options.metric_names,
                timespan=timedelta(hours=options.timespan_hours),
                interval=options.interval,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Metric Baselines") from e
