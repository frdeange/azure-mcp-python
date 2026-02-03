# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-03

### Added

#### Core Framework
- Core framework with authentication, registry, caching, and error handling
- Azure DefaultAzureCredential chain support
- Tool registry with `@register_tool` decorator
- Pydantic-based options validation
- AI Foundry compatible JSON schemas

#### Resource Graph (1 tool)
- `resourcegraph_query` - Execute Azure Resource Graph KQL queries

#### Cosmos DB (7 tools)
- `cosmos_account_list` - List Cosmos DB accounts
- `cosmos_account_get` - Get account details
- `cosmos_database_list` - List databases
- `cosmos_database_get` - Get database details
- `cosmos_container_list` - List containers
- `cosmos_container_get` - Get container details
- `cosmos_item_query` - Query items with SQL

#### Cost Management (7 tools) ⭐ Exclusive
- `cost_query` - Query cost and usage data
- `cost_forecast` - Get cost forecasts
- `cost_usage_by_resource` - Get usage by resource
- `cost_budgets_list` - List budgets
- `cost_budgets_get` - Get budget details
- `cost_recommendations` - Get cost recommendations
- `cost_exports_list` - List cost exports

#### Storage (9 tools)
- `storage_account_list` - List storage accounts
- `storage_account_get` - Get account details
- `storage_container_list` - List containers
- `storage_blob_list` - List blobs
- `storage_blob_read` - Read blob content
- `storage_blob_write` - Write blob content
- `storage_blob_delete` - Delete blobs
- `storage_queue_list` - List queues
- `storage_table_query` - Query table entities

#### Entra ID (18 tools) ⭐ Exclusive
- User tools: `entraid_user_list`, `entraid_user_get`, `entraid_user_groups`, `entraid_user_manager`, `entraid_user_direct_reports`, `entraid_user_app_role_assignments`
- Group tools: `entraid_group_list`, `entraid_group_get`, `entraid_group_members`, `entraid_group_owners`
- App tools: `entraid_app_list`, `entraid_app_get`, `entraid_sp_list`, `entraid_sp_get`
- Security tools: `entraid_sign_in_logs`, `entraid_audit_logs`, `entraid_risky_users`, `entraid_conditional_access_policies`

#### Monitor (17 tools)
- Metrics: `monitor_metrics_list`, `monitor_metrics_get`, `monitor_metric_baselines_get`
- Alerts: `monitor_alerts_list`, `monitor_alerts_get`, `monitor_alerts_history`, `monitor_action_groups_list`, `monitor_action_groups_get`
- Activity: `monitor_activity_log`
- Configuration: `monitor_diagnostic_settings_list`, `monitor_diagnostic_settings_get`, `monitor_data_collection_rules_list`
- Autoscale: `monitor_autoscale_list`, `monitor_autoscale_get`
- Logs: `monitor_logs_query`, `monitor_logs_query_resource`, `monitor_logs_batch_query`

#### Application Insights (8 tools)
- `appinsights_discovery` - Discover App Insights resources
- `appinsights_query` - Execute KQL queries
- `appinsights_traces` - Query trace telemetry
- `appinsights_exceptions` - Query exceptions
- `appinsights_requests` - Query request telemetry
- `appinsights_dependencies` - Query dependency telemetry
- `appinsights_events` - Query custom events

#### RBAC (8 tools)
- `rbac_role_definitions_list` - List role definitions
- `rbac_role_definitions_get` - Get role definition
- `rbac_role_assignments_list` - List role assignments
- `rbac_role_assignments_get` - Get role assignment
- `rbac_role_assignments_create` - Create role assignment
- `rbac_role_assignments_delete` - Delete role assignment
- `rbac_app_role_assignments_list` - List app role assignments
- `rbac_app_role_assignments_user` - Get user's app role assignments

#### Communication Services (7 tools) ⭐ Exclusive
- `communication_resource_list` - List Communication resources
- `communication_resource_get` - Get resource details
- `communication_phonenumber_list` - List phone numbers
- `communication_phonenumber_get` - Get phone number details
- `communication_sms_send` - Send SMS messages
- `communication_email_send` - Send emails
- `communication_email_status` - Check email status

#### Azure AI Search (12 tools) ⭐ Exclusive
- Discovery: `search_service_list`, `search_service_get`
- Index management: `search_index_list`, `search_index_get`, `search_index_stats`
- Search: `search_query`, `search_suggest`, `search_autocomplete`
- Documents: `search_document_get`, `search_document_upload`, `search_document_merge`, `search_document_delete`

### Documentation
- Comprehensive README with tool reference
- Adding tools guide
- Authentication guide
- Testing guide
- AI Foundry deployment guide
- Architecture documentation
