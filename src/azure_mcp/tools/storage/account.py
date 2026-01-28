"""Storage account tools.

Provides tools for listing and getting storage account details.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.storage.service import StorageService


class StorageAccountListOptions(BaseModel):
    """Options for listing storage accounts."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to filter by. Leave empty for all resource groups.",
    )


@register_tool("storage", "account")
class StorageAccountListTool(AzureTool):
    """Tool for listing Azure Storage accounts."""

    @property
    def name(self) -> str:
        return "storage_account_list"

    @property
    def description(self) -> str:
        return (
            "List Azure Storage accounts in a subscription. "
            "Returns account names, locations, SKUs, and access tiers. "
            "Can be filtered by resource group."
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
        return StorageAccountListOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the storage account list query."""
        opts = StorageAccountListOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.list_accounts(
                subscription=opts.subscription,
                resource_group=opts.resource_group,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Accounts") from e


class StorageAccountGetOptions(BaseModel):
    """Options for getting storage account details."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    account_name: str = Field(
        ...,
        description="Name of the storage account to get details for.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group of the account (optional, speeds up lookup).",
    )


@register_tool("storage", "account")
class StorageAccountGetTool(AzureTool):
    """Tool for getting storage account details."""

    @property
    def name(self) -> str:
        return "storage_account_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about an Azure Storage account. "
            "Returns account configuration including endpoints, encryption settings, "
            "network rules, and access tier."
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
        return StorageAccountGetOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the storage account get query."""
        opts = StorageAccountGetOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.get_account(
                subscription=opts.subscription,
                account_name=opts.account_name,
                resource_group=opts.resource_group,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Account") from e
