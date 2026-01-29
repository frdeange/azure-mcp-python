"""Tests for Communication Services tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from azure_mcp.tools.communication.email import (
    CommunicationEmailSendOptions,
    CommunicationEmailSendTool,
    CommunicationEmailStatusOptions,
    CommunicationEmailStatusTool,
)
from azure_mcp.tools.communication.phonenumber import (
    CommunicationPhoneNumberGetOptions,
    CommunicationPhoneNumberGetTool,
    CommunicationPhoneNumberListOptions,
    CommunicationPhoneNumberListTool,
)
from azure_mcp.tools.communication.resource import (
    CommunicationResourceGetOptions,
    CommunicationResourceGetTool,
    CommunicationResourceListOptions,
    CommunicationResourceListTool,
)
from azure_mcp.tools.communication.service import CommunicationService
from azure_mcp.tools.communication.sms import (
    CommunicationSmsSendOptions,
    CommunicationSmsSendTool,
)


# =============================================================================
# communication_resource_list Tests
# =============================================================================


class TestCommunicationResourceListOptions:
    """Tests for CommunicationResourceListOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CommunicationResourceListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""  # AI Foundry compatible
        assert options.limit == 50

    def test_full_options(self):
        """Test creation with all fields."""
        options = CommunicationResourceListOptions(
            subscription="my-sub",
            resource_group="my-rg",
            limit=100,
        )
        assert options.subscription == "my-sub"
        assert options.resource_group == "my-rg"
        assert options.limit == 100

    def test_limit_validation(self):
        """Test that limit must be between 1 and 200."""
        with pytest.raises(ValueError):
            CommunicationResourceListOptions(subscription="sub", limit=0)

        with pytest.raises(ValueError):
            CommunicationResourceListOptions(subscription="sub", limit=201)


class TestCommunicationResourceListTool:
    """Tests for CommunicationResourceListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationResourceListTool()
        assert tool.name == "communication_resource_list"
        assert "Communication Services" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationResourceListTool()
        options = CommunicationResourceListOptions(subscription="my-sub")

        with patch.object(CommunicationService, "list_communication_resources") as mock_list:
            mock_list.return_value = [
                {"name": "comm1", "endpoint": "mycomm.communication.azure.com"}
            ]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                subscription="my-sub",
                resource_group="",
                limit=50,
            )
            assert len(result) == 1
            assert result[0]["name"] == "comm1"


# =============================================================================
# communication_resource_get Tests
# =============================================================================


class TestCommunicationResourceGetOptions:
    """Tests for CommunicationResourceGetOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CommunicationResourceGetOptions(
            subscription="my-sub",
            resource_name="my-comm",
        )
        assert options.subscription == "my-sub"
        assert options.resource_name == "my-comm"
        assert options.resource_group == ""

    def test_full_options(self):
        """Test creation with all fields."""
        options = CommunicationResourceGetOptions(
            subscription="my-sub",
            resource_name="my-comm",
            resource_group="my-rg",
        )
        assert options.resource_group == "my-rg"


class TestCommunicationResourceGetTool:
    """Tests for CommunicationResourceGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationResourceGetTool()
        assert tool.name == "communication_resource_get"
        assert "endpoint" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationResourceGetTool()
        options = CommunicationResourceGetOptions(
            subscription="my-sub",
            resource_name="my-comm",
        )

        with patch.object(CommunicationService, "get_communication_resource") as mock_get:
            mock_get.return_value = {
                "name": "my-comm",
                "endpoint": "mycomm.communication.azure.com",
            }

            result = await tool.execute(options)

            mock_get.assert_called_once_with(
                subscription="my-sub",
                resource_name="my-comm",
                resource_group="",
            )
            assert result["name"] == "my-comm"

    @pytest.mark.asyncio
    async def test_execute_not_found(self, patch_credential):
        """Test that execute returns error when not found."""
        tool = CommunicationResourceGetTool()
        options = CommunicationResourceGetOptions(
            subscription="my-sub",
            resource_name="nonexistent",
        )

        with patch.object(CommunicationService, "get_communication_resource") as mock_get:
            mock_get.return_value = None

            result = await tool.execute(options)

            assert "error" in result
            assert "nonexistent" in result["error"]


# =============================================================================
# communication_phonenumber_list Tests
# =============================================================================


class TestCommunicationPhoneNumberListOptions:
    """Tests for CommunicationPhoneNumberListOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CommunicationPhoneNumberListOptions(
            endpoint="https://mycomm.communication.azure.com"
        )
        assert options.endpoint == "https://mycomm.communication.azure.com"


class TestCommunicationPhoneNumberListTool:
    """Tests for CommunicationPhoneNumberListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationPhoneNumberListTool()
        assert tool.name == "communication_phonenumber_list"
        assert "phone" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationPhoneNumberListTool()
        options = CommunicationPhoneNumberListOptions(
            endpoint="https://mycomm.communication.azure.com"
        )

        with patch.object(CommunicationService, "list_phone_numbers") as mock_list:
            mock_list.return_value = [
                {
                    "phone_number": "+14255550100",
                    "capabilities": {"sms": "outbound", "calling": "none"},
                }
            ]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                endpoint="https://mycomm.communication.azure.com"
            )
            assert len(result) == 1
            assert result[0]["phone_number"] == "+14255550100"


# =============================================================================
# communication_phonenumber_get Tests
# =============================================================================


class TestCommunicationPhoneNumberGetOptions:
    """Tests for CommunicationPhoneNumberGetOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CommunicationPhoneNumberGetOptions(
            endpoint="https://mycomm.communication.azure.com",
            phone_number="+14255550100",
        )
        assert options.endpoint == "https://mycomm.communication.azure.com"
        assert options.phone_number == "+14255550100"


class TestCommunicationPhoneNumberGetTool:
    """Tests for CommunicationPhoneNumberGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationPhoneNumberGetTool()
        assert tool.name == "communication_phonenumber_get"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationPhoneNumberGetTool()
        options = CommunicationPhoneNumberGetOptions(
            endpoint="https://mycomm.communication.azure.com",
            phone_number="+14255550100",
        )

        with patch.object(CommunicationService, "get_phone_number") as mock_get:
            mock_get.return_value = {
                "phone_number": "+14255550100",
                "capabilities": {"sms": "outbound", "calling": "none"},
            }

            result = await tool.execute(options)

            mock_get.assert_called_once_with(
                endpoint="https://mycomm.communication.azure.com",
                phone_number="+14255550100",
            )
            assert result["phone_number"] == "+14255550100"


# =============================================================================
# communication_sms_send Tests
# =============================================================================


class TestCommunicationSmsSendOptions:
    """Tests for CommunicationSmsSendOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CommunicationSmsSendOptions(
            endpoint="https://mycomm.communication.azure.com",
            from_number="+14255550100",
            to=["+14255550101"],
            message="Hello!",
        )
        assert options.endpoint == "https://mycomm.communication.azure.com"
        assert options.from_number == "+14255550100"
        assert options.to == ["+14255550101"]
        assert options.message == "Hello!"
        assert options.enable_delivery_report is False
        assert options.tag == ""

    def test_full_options(self):
        """Test creation with all fields."""
        options = CommunicationSmsSendOptions(
            endpoint="https://mycomm.communication.azure.com",
            from_number="+14255550100",
            to=["+14255550101", "+14255550102"],
            message="Hello!",
            enable_delivery_report=True,
            tag="campaign-123",
        )
        assert len(options.to) == 2
        assert options.enable_delivery_report is True
        assert options.tag == "campaign-123"


class TestCommunicationSmsSendTool:
    """Tests for CommunicationSmsSendTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationSmsSendTool()
        assert tool.name == "communication_sms_send"
        assert "SMS" in tool.description
        assert tool.metadata.read_only is False  # Write operation
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is False  # Sending twice = two messages

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationSmsSendTool()
        options = CommunicationSmsSendOptions(
            endpoint="https://mycomm.communication.azure.com",
            from_number="+14255550100",
            to=["+14255550101"],
            message="Hello!",
        )

        with patch.object(CommunicationService, "send_sms") as mock_send:
            mock_send.return_value = [
                {
                    "to": "+14255550101",
                    "message_id": "msg-123",
                    "successful": True,
                }
            ]

            result = await tool.execute(options)

            mock_send.assert_called_once_with(
                endpoint="https://mycomm.communication.azure.com",
                from_number="+14255550100",
                to=["+14255550101"],
                message="Hello!",
                enable_delivery_report=False,
                tag="",
            )
            assert len(result) == 1
            assert result[0]["successful"] is True


# =============================================================================
# communication_email_send Tests
# =============================================================================


class TestCommunicationEmailSendOptions:
    """Tests for CommunicationEmailSendOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CommunicationEmailSendOptions(
            endpoint="https://mycomm.communication.azure.com",
            from_address="noreply@contoso.com",
            to=["user@example.com"],
            subject="Test",
            body="Hello!",
        )
        assert options.endpoint == "https://mycomm.communication.azure.com"
        assert options.from_address == "noreply@contoso.com"
        assert options.to == ["user@example.com"]
        assert options.subject == "Test"
        assert options.body == "Hello!"
        assert options.is_html is False
        assert options.sender_name == ""
        assert options.cc == []
        assert options.bcc == []
        assert options.reply_to == []

    def test_full_options(self):
        """Test creation with all fields."""
        options = CommunicationEmailSendOptions(
            endpoint="https://mycomm.communication.azure.com",
            from_address="noreply@contoso.com",
            to=["user@example.com"],
            subject="Test",
            body="<h1>Hello!</h1>",
            is_html=True,
            sender_name="Contoso Support",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@contoso.com"],
        )
        assert options.is_html is True
        assert options.sender_name == "Contoso Support"
        assert options.cc == ["cc@example.com"]


class TestCommunicationEmailSendTool:
    """Tests for CommunicationEmailSendTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationEmailSendTool()
        assert tool.name == "communication_email_send"
        assert "email" in tool.description.lower()
        assert tool.metadata.read_only is False  # Write operation
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is False  # Sending twice = two emails

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationEmailSendTool()
        options = CommunicationEmailSendOptions(
            endpoint="https://mycomm.communication.azure.com",
            from_address="noreply@contoso.com",
            to=["user@example.com"],
            subject="Test",
            body="Hello!",
        )

        with patch.object(CommunicationService, "send_email") as mock_send:
            mock_send.return_value = {
                "operation_id": "op-123",
                "message_id": "msg-456",
                "status": "Running",
            }

            result = await tool.execute(options)

            mock_send.assert_called_once_with(
                endpoint="https://mycomm.communication.azure.com",
                from_address="noreply@contoso.com",
                to=["user@example.com"],
                subject="Test",
                body="Hello!",
                is_html=False,
                sender_name="",
                cc=None,
                bcc=None,
                reply_to=None,
            )
            assert result["operation_id"] == "op-123"


# =============================================================================
# communication_email_status Tests
# =============================================================================


class TestCommunicationEmailStatusOptions:
    """Tests for CommunicationEmailStatusOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CommunicationEmailStatusOptions(
            endpoint="https://mycomm.communication.azure.com",
            operation_id="op-123",
        )
        assert options.endpoint == "https://mycomm.communication.azure.com"
        assert options.operation_id == "op-123"


class TestCommunicationEmailStatusTool:
    """Tests for CommunicationEmailStatusTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CommunicationEmailStatusTool()
        assert tool.name == "communication_email_status"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CommunicationEmailStatusTool()
        options = CommunicationEmailStatusOptions(
            endpoint="https://mycomm.communication.azure.com",
            operation_id="op-123",
        )

        with patch.object(CommunicationService, "get_email_status") as mock_get:
            mock_get.return_value = {
                "operation_id": "op-123",
                "note": "Email delivery status...",
            }

            result = await tool.execute(options)

            mock_get.assert_called_once_with(
                endpoint="https://mycomm.communication.azure.com",
                operation_id="op-123",
            )
            assert result["operation_id"] == "op-123"


# =============================================================================
# Service Tests
# =============================================================================


class TestCommunicationService:
    """Tests for CommunicationService."""

    @pytest.mark.asyncio
    async def test_list_communication_resources_uses_resource_graph(self, patch_credential):
        """Test that list_communication_resources uses Resource Graph."""
        service = CommunicationService()

        with patch.object(service, "execute_resource_graph_query") as mock_query:
            with patch.object(service, "resolve_subscription") as mock_resolve:
                mock_resolve.return_value = "sub-guid-123"
                mock_query.return_value = {
                    "data": [
                        {"name": "comm1", "endpoint": "comm1.communication.azure.com"}
                    ]
                }

                result = await service.list_communication_resources(subscription="my-sub")

                # Verify subscription was resolved
                mock_resolve.assert_called_once_with("my-sub")

                # Verify Resource Graph was used
                mock_query.assert_called_once()
                call_args = mock_query.call_args
                assert "microsoft.communication/communicationservices" in call_args.kwargs["query"].lower()
                assert call_args.kwargs["subscriptions"] == ["sub-guid-123"]

                assert len(result) == 1
                assert result[0]["name"] == "comm1"

    @pytest.mark.asyncio
    async def test_get_communication_resource_uses_resource_graph(self, patch_credential):
        """Test that get_communication_resource uses Resource Graph."""
        service = CommunicationService()

        with patch.object(service, "execute_resource_graph_query") as mock_query:
            with patch.object(service, "resolve_subscription") as mock_resolve:
                mock_resolve.return_value = "sub-guid-123"
                mock_query.return_value = {
                    "data": [
                        {"name": "my-comm", "endpoint": "mycomm.communication.azure.com"}
                    ]
                }

                result = await service.get_communication_resource(
                    subscription="my-sub",
                    resource_name="my-comm",
                )

                # Verify Resource Graph was used with name filter
                mock_query.assert_called_once()
                call_args = mock_query.call_args
                assert "my-comm" in call_args.kwargs["query"]

                assert result is not None
                assert result["name"] == "my-comm"

    @pytest.mark.asyncio
    async def test_get_communication_resource_not_found(self, patch_credential):
        """Test that get_communication_resource returns None when not found."""
        service = CommunicationService()

        with patch.object(service, "execute_resource_graph_query") as mock_query:
            with patch.object(service, "resolve_subscription") as mock_resolve:
                mock_resolve.return_value = "sub-guid-123"
                mock_query.return_value = {"data": []}

                result = await service.get_communication_resource(
                    subscription="my-sub",
                    resource_name="nonexistent",
                )

                assert result is None
