"""Communication Services resource discovery tools.

Tools for listing and getting Azure Communication Services resources.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool

from .service import CommunicationService


class CommunicationResourceListOptions(BaseModel):
    """Options for listing Communication Services resources."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to filter by. Leave empty for all.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of resources to return",
    )


class CommunicationResourceGetOptions(BaseModel):
    """Options for getting a specific Communication Services resource."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or name",
    )
    resource_name: str = Field(
        ...,
        description="Name of the Communication Services resource",
    )
    resource_group: str = Field(
        default="",
        description="Resource group containing the resource. Leave empty to search all.",
    )


@register_tool("communication", "resource")
class CommunicationResourceListTool(AzureTool):
    """Tool for listing Azure Communication Services resources."""

    @property
    def name(self) -> str:
        return "communication_resource_list"

    @property
    def description(self) -> str:
        return (
            "List Azure Communication Services resources in a subscription. "
            "Returns resource names, endpoints, locations, and provisioning state. "
            "Use this to discover Communication Services endpoints before sending SMS or email."
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
        return CommunicationResourceListOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the list operation."""
        opts = CommunicationResourceListOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            return await service.list_communication_resources(
                subscription=opts.subscription,
                resource_group=opts.resource_group,
                limit=opts.limit,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Communication Services") from e


@register_tool("communication", "resource")
class CommunicationResourceGetTool(AzureTool):
    """Tool for getting a specific Azure Communication Services resource."""

    @property
    def name(self) -> str:
        return "communication_resource_get"

    @property
    def description(self) -> str:
        return (
            "Get details of a specific Azure Communication Services resource. "
            "Returns the endpoint URL needed for SMS, email, and other operations. "
            "Use the endpoint from this tool when calling communication_sms_send or communication_email_send."
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
        return CommunicationResourceGetOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the get operation."""
        opts = CommunicationResourceGetOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            result = await service.get_communication_resource(
                subscription=opts.subscription,
                resource_name=opts.resource_name,
                resource_group=opts.resource_group,
            )
            if result is None:
                return {"error": f"Communication Services resource '{opts.resource_name}' not found"}
            return result
        except Exception as e:
            raise handle_azure_error(e, resource="Communication Services") from e
