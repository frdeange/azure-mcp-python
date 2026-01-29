"""Communication Services SMS tools.

Tools for sending SMS messages.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool

from .service import CommunicationService


class CommunicationSmsSendOptions(BaseModel):
    """Options for sending SMS messages."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure Communication Services endpoint URL "
            "(e.g., 'https://myresource.communication.azure.com'). "
            "Obtain this from communication_resource_list or communication_resource_get."
        ),
    )
    from_number: str = Field(
        ...,
        description=(
            "SMS-enabled phone number in E.164 format (e.g., '+14255550100'). "
            "This must be a phone number purchased for the Communication Services resource. "
            "Use communication_phonenumber_list to see available numbers."
        ),
    )
    to: list[str] = Field(
        ...,
        description=(
            "List of recipient phone numbers in E.164 format. "
            "Can send to one or multiple recipients."
        ),
    )
    message: str = Field(
        ...,
        description="The SMS message content to send.",
    )
    enable_delivery_report: bool = Field(
        default=False,
        description=(
            "Enable delivery reporting for sent messages. "
            "Delivery reports are sent via Azure Event Grid."
        ),
    )
    tag: str = Field(
        default="",
        description="Custom tag for tracking and analytics. Leave empty if not needed.",
    )


@register_tool("communication", "sms")
class CommunicationSmsSendTool(AzureTool):
    """Tool for sending SMS messages."""

    @property
    def name(self) -> str:
        return "communication_sms_send"

    @property
    def description(self) -> str:
        return (
            "Send SMS messages to one or more recipients via Azure Communication Services. "
            "Requires a valid Communication Services endpoint and an SMS-enabled phone number. "
            "Use communication_resource_list to get the endpoint and "
            "communication_phonenumber_list to get available sender phone numbers. "
            "Returns send status for each recipient."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=False,  # Sending twice = two messages
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CommunicationSmsSendOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the SMS send operation."""
        opts = CommunicationSmsSendOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            return await service.send_sms(
                endpoint=opts.endpoint,
                from_number=opts.from_number,
                to=opts.to,
                message=opts.message,
                enable_delivery_report=opts.enable_delivery_report,
                tag=opts.tag,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="SMS") from e
