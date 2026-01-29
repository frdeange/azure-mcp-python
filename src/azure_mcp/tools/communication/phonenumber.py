"""Communication Services phone number tools.

Tools for listing and getting phone numbers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool

from .service import CommunicationService


class CommunicationPhoneNumberListOptions(BaseModel):
    """Options for listing phone numbers."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure Communication Services endpoint URL "
            "(e.g., 'https://myresource.communication.azure.com'). "
            "Obtain this from communication_resource_list or communication_resource_get."
        ),
    )


class CommunicationPhoneNumberGetOptions(BaseModel):
    """Options for getting a specific phone number."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure Communication Services endpoint URL. "
            "Obtain this from communication_resource_list or communication_resource_get."
        ),
    )
    phone_number: str = Field(
        ...,
        description=(
            "Phone number in E.164 format (e.g., '+14255550100'). "
            "Obtain from communication_phonenumber_list."
        ),
    )


@register_tool("communication", "phonenumber")
class CommunicationPhoneNumberListTool(AzureTool):
    """Tool for listing purchased phone numbers."""

    @property
    def name(self) -> str:
        return "communication_phonenumber_list"

    @property
    def description(self) -> str:
        return (
            "List all purchased phone numbers for an Azure Communication Services resource. "
            "Returns phone numbers with their capabilities (SMS, calling). "
            "Use communication_resource_list first to get the endpoint. "
            "Use the phone numbers from this tool as the 'from' number when sending SMS."
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
        return CommunicationPhoneNumberListOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the list operation."""
        opts = CommunicationPhoneNumberListOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            return await service.list_phone_numbers(endpoint=opts.endpoint)
        except Exception as e:
            raise handle_azure_error(e, resource="Phone Number") from e


@register_tool("communication", "phonenumber")
class CommunicationPhoneNumberGetTool(AzureTool):
    """Tool for getting details of a specific phone number."""

    @property
    def name(self) -> str:
        return "communication_phonenumber_get"

    @property
    def description(self) -> str:
        return (
            "Get details of a specific phone number including capabilities and cost. "
            "Use this to verify a phone number supports SMS before sending. "
            "The phone number must be in E.164 format (e.g., '+14255550100')."
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
        return CommunicationPhoneNumberGetOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the get operation."""
        opts = CommunicationPhoneNumberGetOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            return await service.get_phone_number(
                endpoint=opts.endpoint,
                phone_number=opts.phone_number,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Phone Number") from e
