"""Communication Services service layer.

Provides CommunicationService for Azure Communication Services operations.
Uses AAD authentication only (DefaultAzureCredential) for security.

Architecture: Uses async SDK clients (.aio modules) for non-blocking I/O.
See Issue #78 for async-first architecture decision.
"""

from __future__ import annotations

from typing import Any

from azure_mcp.core.base import AzureService


class CommunicationService(AzureService):
    """
    Service for Azure Communication Services operations.

    Uses azure-communication-* async SDKs (.aio) with AAD authentication.
    Resource discovery is done via Resource Graph (base class methods).

    Architecture Note:
        All Communication Services SDKs have async versions available:
        - azure.communication.email.aio.EmailClient
        - azure.communication.sms.aio.SmsClient
        - azure.communication.phonenumbers.aio.PhoneNumbersClient

        Using async clients prevents blocking the event loop during
        long-running operations like email sending (2-5 seconds).
    """

    # -------------------------------------------------------------------------
    # Resource Discovery (via Resource Graph)
    # -------------------------------------------------------------------------

    async def list_communication_resources(
        self,
        subscription: str,
        resource_group: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List Communication Services resources using Resource Graph.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            limit: Maximum number of results.

        Returns:
            List of Communication Services resources with endpoints.
        """
        sub_id = await self.resolve_subscription(subscription)

        query = """
        resources
        | where type =~ 'microsoft.communication/communicationservices'
        | project
            name,
            id,
            resourceGroup,
            location,
            subscriptionId,
            endpoint = properties.hostName,
            dataLocation = properties.dataLocation,
            provisioningState = properties.provisioningState
        | order by name
        """
        query += f" | limit {limit}"

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
            top=limit,
        )
        return result.get("data", [])

    async def get_communication_resource(
        self,
        subscription: str,
        resource_name: str,
        resource_group: str = "",
    ) -> dict[str, Any] | None:
        """
        Get a specific Communication Services resource.

        Args:
            subscription: Subscription ID or name.
            resource_name: Name of the Communication Services resource.
            resource_group: Optional resource group filter.

        Returns:
            Resource details with endpoint, or None if not found.
        """
        sub_id = await self.resolve_subscription(subscription)

        query = f"""
        resources
        | where type =~ 'microsoft.communication/communicationservices'
        | where name =~ '{self._escape_kql(resource_name)}'
        """
        if resource_group:
            query += f" | where resourceGroup =~ '{self._escape_kql(resource_group)}'"

        query += """
        | project
            name,
            id,
            resourceGroup,
            location,
            subscriptionId,
            endpoint = properties.hostName,
            dataLocation = properties.dataLocation,
            provisioningState = properties.provisioningState,
            immutableResourceId = properties.immutableResourceId
        """

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
            top=1,
        )
        data = result.get("data", [])
        return data[0] if data else None

    # -------------------------------------------------------------------------
    # Phone Numbers (async)
    # -------------------------------------------------------------------------

    async def list_phone_numbers(
        self,
        endpoint: str,
    ) -> list[dict[str, Any]]:
        """
        List all purchased phone numbers for a Communication Services resource.

        Args:
            endpoint: Communication Services endpoint
                      (e.g., https://myresource.communication.azure.com).

        Returns:
            List of phone numbers with capabilities.
        """
        from azure.communication.phonenumbers.aio import PhoneNumbersClient

        credential = self.get_credential()
        phone_numbers = []

        async with PhoneNumbersClient(endpoint, credential) as client:
            async for phone in client.list_purchased_phone_numbers():
                phone_numbers.append(
                    {
                        "phone_number": phone.phone_number,
                        "country_code": phone.country_code,
                        "phone_number_type": phone.phone_number_type.value
                        if hasattr(phone.phone_number_type, "value")
                        else str(phone.phone_number_type),
                        "capabilities": {
                            "calling": phone.capabilities.calling.value
                            if hasattr(phone.capabilities.calling, "value")
                            else str(phone.capabilities.calling),
                            "sms": phone.capabilities.sms.value
                            if hasattr(phone.capabilities.sms, "value")
                            else str(phone.capabilities.sms),
                        },
                        "assignment_type": phone.assignment_type.value
                        if hasattr(phone.assignment_type, "value")
                        else str(phone.assignment_type),
                        "purchase_date": phone.purchase_date.isoformat()
                        if phone.purchase_date
                        else None,
                    }
                )

        return phone_numbers

    async def get_phone_number(
        self,
        endpoint: str,
        phone_number: str,
    ) -> dict[str, Any]:
        """
        Get details for a specific phone number.

        Args:
            endpoint: Communication Services endpoint.
            phone_number: Phone number in E.164 format (e.g., +14255550100).

        Returns:
            Phone number details with capabilities.
        """
        from azure.communication.phonenumbers.aio import PhoneNumbersClient

        credential = self.get_credential()

        async with PhoneNumbersClient(endpoint, credential) as client:
            phone = await client.get_purchased_phone_number(phone_number)

            return {
                "phone_number": phone.phone_number,
                "country_code": phone.country_code,
                "phone_number_type": phone.phone_number_type.value
                if hasattr(phone.phone_number_type, "value")
                else str(phone.phone_number_type),
                "capabilities": {
                    "calling": phone.capabilities.calling.value
                    if hasattr(phone.capabilities.calling, "value")
                    else str(phone.capabilities.calling),
                    "sms": phone.capabilities.sms.value
                    if hasattr(phone.capabilities.sms, "value")
                    else str(phone.capabilities.sms),
                },
                "assignment_type": phone.assignment_type.value
                if hasattr(phone.assignment_type, "value")
                else str(phone.assignment_type),
                "purchase_date": phone.purchase_date.isoformat()
                if phone.purchase_date
                else None,
                "cost": {
                    "amount": phone.cost.amount if phone.cost else None,
                    "currency_code": phone.cost.currency_code if phone.cost else None,
                    "billing_frequency": phone.cost.billing_frequency.value
                    if phone.cost and hasattr(phone.cost.billing_frequency, "value")
                    else str(phone.cost.billing_frequency)
                    if phone.cost
                    else None,
                },
            }

    # -------------------------------------------------------------------------
    # SMS (async)
    # -------------------------------------------------------------------------

    async def send_sms(
        self,
        endpoint: str,
        from_number: str,
        to: list[str],
        message: str,
        enable_delivery_report: bool = False,
        tag: str = "",
    ) -> list[dict[str, Any]]:
        """
        Send SMS messages to one or more recipients.

        Args:
            endpoint: Communication Services endpoint.
            from_number: SMS-enabled phone number in E.164 format.
            to: List of recipient phone numbers in E.164 format.
            message: SMS message content.
            enable_delivery_report: Whether to enable delivery reporting.
            tag: Custom tag for tracking.

        Returns:
            List of send results for each recipient.
        """
        from azure.communication.sms.aio import SmsClient

        credential = self.get_credential()

        # Build options
        send_options = {}
        if enable_delivery_report:
            send_options["enable_delivery_report"] = True
        if tag:
            send_options["tag"] = tag

        async with SmsClient(endpoint, credential) as client:
            responses = await client.send(
                from_=from_number,
                to=to,
                message=message,
                **send_options,
            )

            return [
                {
                    "to": response.to,
                    "message_id": response.message_id,
                    "successful": response.successful,
                    "http_status_code": response.http_status_code,
                    "error_message": response.error_message if not response.successful else None,
                }
                for response in responses
            ]

    # -------------------------------------------------------------------------
    # Email (async)
    # -------------------------------------------------------------------------

    async def send_email(
        self,
        endpoint: str,
        from_address: str,
        to: list[str],
        subject: str,
        body: str,
        is_html: bool = False,
        sender_name: str = "",
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Send an email message.

        Uses async EmailClient with AsyncLROPoller for non-blocking operation.
        Email sending typically takes 2-5 seconds; async prevents blocking
        other requests during this time.

        Args:
            endpoint: Communication Services endpoint.
            from_address: Sender email (must be from verified domain).
            to: List of recipient email addresses.
            subject: Email subject.
            body: Email body content.
            is_html: Whether body is HTML content.
            sender_name: Sender display name.
            cc: List of CC recipients.
            bcc: List of BCC recipients.
            reply_to: List of reply-to addresses.

        Returns:
            Send operation result with operation ID and status.
        """
        from azure.communication.email.aio import EmailClient

        credential = self.get_credential()

        # Build recipients
        recipients: dict[str, Any] = {
            "to": [{"address": addr} for addr in to],
        }
        if cc:
            recipients["cc"] = [{"address": addr} for addr in cc]
        if bcc:
            recipients["bcc"] = [{"address": addr} for addr in bcc]

        # Build content
        content: dict[str, str] = {"subject": subject}
        if is_html:
            content["html"] = body
        else:
            content["plainText"] = body

        # Build message
        message: dict[str, Any] = {
            "senderAddress": from_address,
            "recipients": recipients,
            "content": content,
        }

        if reply_to:
            message["replyTo"] = [{"address": addr} for addr in reply_to]

        # Send using async client with context manager
        async with EmailClient(endpoint, credential) as client:
            # begin_send returns AsyncLROPoller
            poller = await client.begin_send(message)
            # await result() to get the final status without blocking
            result = await poller.result()

            # The result contains the operation_id and status
            # Note: In the Email SDK, the 'id' in result is the operation/message ID
            return {
                "operation_id": result.get("id")
                if isinstance(result, dict)
                else getattr(result, "id", None),
                "message_id": result.get("id")
                if isinstance(result, dict)
                else getattr(result, "id", None),
                "status": result.get("status")
                if isinstance(result, dict)
                else getattr(result, "status", None),
            }

    async def get_email_status(
        self,
        endpoint: str,
        operation_id: str,
    ) -> dict[str, Any]:
        """
        Get the status of an email send operation.

        Note: This uses the operation ID from send_email result.
        The Email SDK tracks send operations via polling.

        Args:
            endpoint: Communication Services endpoint.
            operation_id: Operation ID from send_email result.

        Returns:
            Operation status details.
        """
        # Note: The Azure Communication Email SDK doesn't provide a direct
        # way to check status after the fact. Status tracking is done via:
        # 1. The initial poller.result() during send
        # 2. Azure Event Grid webhooks for delivery events
        return {
            "operation_id": operation_id,
            "note": (
                "Email delivery status is tracked via Azure Event Grid webhooks. "
                "Use Azure Monitor or Event Grid to track delivery events."
            ),
        }
