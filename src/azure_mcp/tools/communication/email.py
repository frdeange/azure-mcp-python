"""Communication Services email tools.

Tools for sending and tracking email messages.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool

from .service import CommunicationService


class CommunicationEmailSendOptions(BaseModel):
    """Options for sending email messages."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure Communication Services endpoint URL "
            "(e.g., 'https://myresource.communication.azure.com'). "
            "Obtain this from communication_resource_list or communication_resource_get."
        ),
    )
    from_address: str = Field(
        ...,
        description=(
            "Sender email address. Must be from a verified domain configured "
            "in the Communication Services resource (e.g., 'noreply@contoso.com')."
        ),
    )
    to: list[str] = Field(
        ...,
        description="List of recipient email addresses.",
    )
    subject: str = Field(
        ...,
        description="Email subject line.",
    )
    body: str = Field(
        ...,
        description="Email body content (plain text or HTML based on is_html flag).",
    )
    is_html: bool = Field(
        default=False,
        description="Whether the body content is HTML. Set to true for HTML emails.",
    )
    sender_name: str = Field(
        default="",
        description="Sender display name (e.g., 'Contoso Support'). Leave empty for no display name.",
    )
    cc: list[str] = Field(
        default_factory=list,
        description="List of CC recipient email addresses. Pass empty list if none.",
    )
    bcc: list[str] = Field(
        default_factory=list,
        description="List of BCC recipient email addresses. Pass empty list if none.",
    )
    reply_to: list[str] = Field(
        default_factory=list,
        description="List of reply-to email addresses. Pass empty list to use sender address.",
    )


class CommunicationEmailStatusOptions(BaseModel):
    """Options for getting email send operation status."""

    endpoint: str = Field(
        ...,
        description="Azure Communication Services endpoint URL.",
    )
    operation_id: str = Field(
        ...,
        description=(
            "The operation ID returned from communication_email_send. "
            "Use this to track the delivery status of a sent email."
        ),
    )


@register_tool("communication", "email")
class CommunicationEmailSendTool(AzureTool):
    """Tool for sending email messages."""

    @property
    def name(self) -> str:
        return "communication_email_send"

    @property
    def description(self) -> str:
        return (
            "Send email messages via Azure Communication Services. "
            "Supports HTML content, CC/BCC recipients, custom reply-to addresses, and sender display names. "
            "The sender address must be from a verified domain configured in the Communication Services resource. "
            "Use communication_resource_list to get the endpoint. "
            "Returns an operation ID that can be used to track delivery status."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=False,  # Sending twice = two emails
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CommunicationEmailSendOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the email send operation."""
        opts = CommunicationEmailSendOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            return await service.send_email(
                endpoint=opts.endpoint,
                from_address=opts.from_address,
                to=opts.to,
                subject=opts.subject,
                body=opts.body,
                is_html=opts.is_html,
                sender_name=opts.sender_name,
                cc=opts.cc if opts.cc else None,
                bcc=opts.bcc if opts.bcc else None,
                reply_to=opts.reply_to if opts.reply_to else None,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Email") from e


@register_tool("communication", "email")
class CommunicationEmailStatusTool(AzureTool):
    """Tool for getting email send operation status."""

    @property
    def name(self) -> str:
        return "communication_email_status"

    @property
    def description(self) -> str:
        return (
            "Get the status of an email send operation. "
            "Use the operation_id returned from communication_email_send. "
            "Note: Full delivery tracking requires Azure Event Grid integration."
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
        return CommunicationEmailStatusOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the status check operation."""
        opts = CommunicationEmailStatusOptions.model_validate(options.model_dump())
        service = CommunicationService()

        try:
            return await service.get_email_status(
                endpoint=opts.endpoint,
                operation_id=opts.operation_id,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Email") from e
