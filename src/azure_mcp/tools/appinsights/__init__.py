"""Application Insights tools for Azure MCP Server.

This module provides tools for querying Application Insights data:
- Discovery: List and get Application Insights resources
- Query: Run custom KQL queries
- Traces: Query application traces/logs
- Exceptions: Query exception telemetry
- Requests: Query HTTP request telemetry
- Dependencies: Query dependency calls (SQL, HTTP, etc.)
- Events: Query custom events

All query tools use the same LogsQueryClient as Azure Monitor logs,
but target Application Insights resources directly via resource ID.
"""

from azure_mcp.tools.appinsights.dependencies import AppInsightsDependenciesQueryTool
from azure_mcp.tools.appinsights.discovery import (
    AppInsightsGetTool,
    AppInsightsListTool,
)
from azure_mcp.tools.appinsights.events import AppInsightsEventsQueryTool
from azure_mcp.tools.appinsights.exceptions import AppInsightsExceptionsQueryTool
from azure_mcp.tools.appinsights.query import AppInsightsQueryTool
from azure_mcp.tools.appinsights.requests import AppInsightsRequestsQueryTool
from azure_mcp.tools.appinsights.traces import AppInsightsTracesQueryTool

__all__ = [
    # Discovery (2 tools)
    "AppInsightsListTool",
    "AppInsightsGetTool",
    # Query (1 tool)
    "AppInsightsQueryTool",
    # Traces (1 tool)
    "AppInsightsTracesQueryTool",
    # Exceptions (1 tool)
    "AppInsightsExceptionsQueryTool",
    # Requests (1 tool)
    "AppInsightsRequestsQueryTool",
    # Dependencies (1 tool)
    "AppInsightsDependenciesQueryTool",
    # Events (1 tool)
    "AppInsightsEventsQueryTool",
]
