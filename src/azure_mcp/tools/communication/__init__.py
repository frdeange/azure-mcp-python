"""Azure Communication Services tools.

Provides MCP tools for Azure Communication Services:
- Resource discovery (list/get)
- Phone number management (list/get)
- SMS sending
- Email sending and status tracking
"""

from azure_mcp.tools.communication.email import (
    CommunicationEmailSendTool,
    CommunicationEmailStatusTool,
)
from azure_mcp.tools.communication.phonenumber import (
    CommunicationPhoneNumberGetTool,
    CommunicationPhoneNumberListTool,
)
from azure_mcp.tools.communication.resource import (
    CommunicationResourceGetTool,
    CommunicationResourceListTool,
)
from azure_mcp.tools.communication.sms import CommunicationSmsSendTool

__all__ = [
    # Resource discovery
    "CommunicationResourceListTool",
    "CommunicationResourceGetTool",
    # Phone numbers
    "CommunicationPhoneNumberListTool",
    "CommunicationPhoneNumberGetTool",
    # SMS
    "CommunicationSmsSendTool",
    # Email
    "CommunicationEmailSendTool",
    "CommunicationEmailStatusTool",
]
