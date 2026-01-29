"""Azure Monitor service for querying logs, metrics, and managing alerts."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from azure_mcp.core.base import AzureService
from azure_mcp.core.errors import (
    AzureResourceError,
    handle_azure_error,
)


class MonitorService(AzureService):
    """Service for Azure Monitor operations.

    Provides methods for:
    - Querying Log Analytics workspaces (KQL)
    - Querying resource metrics
    - Listing activity logs
    - Managing alerts and autoscale settings
    """

    def _check_monitor_query_sdk(self) -> None:
        """Check if azure-monitor-query is installed."""
        try:
            import azure.monitor.query  # noqa: F401
        except ImportError:
            raise ImportError(
                "azure-monitor-query is not installed. "
                "Install it with: pip install azure-mcp[monitor]"
            )

    def _check_monitor_mgmt_sdk(self) -> None:
        """Check if azure-mgmt-monitor is installed."""
        try:
            import azure.mgmt.monitor  # noqa: F401
        except ImportError:
            raise ImportError(
                "azure-mgmt-monitor is not installed. "
                "Install it with: pip install azure-mcp[monitor]"
            )

    # =========================================================================
    # Log Analytics Queries
    # =========================================================================

    async def query_logs(
        self,
        workspace_id: str,
        query: str,
        timespan: timedelta = timedelta(hours=24),
        include_statistics: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a KQL query against a Log Analytics workspace.

        Args:
            workspace_id: The Log Analytics workspace ID (GUID).
            query: The KQL query to execute.
            timespan: Time range for the query.
            include_statistics: Whether to include query statistics.

        Returns:
            Query results with tables and optional statistics.
        """
        self._check_monitor_query_sdk()
        from azure.monitor.query.aio import LogsQueryClient
        from azure.monitor.query import LogsQueryStatus

        credential = self.get_credential()
        client = LogsQueryClient(credential)

        try:
            response = await client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=timespan,
                include_statistics=include_statistics,
            )

            result: dict[str, Any] = {"tables": [], "status": "success"}

            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    table_data = {
                        "name": table.name,
                        "columns": [col.name for col in table.columns],
                        "rows": [list(row) for row in table.rows],
                    }
                    result["tables"].append(table_data)

                if include_statistics and response.statistics:
                    result["statistics"] = response.statistics
            elif response.status == LogsQueryStatus.PARTIAL:
                result["status"] = "partial"
                result["error"] = str(response.partial_error)
                for table in response.partial_data:
                    table_data = {
                        "name": table.name,
                        "columns": [col.name for col in table.columns],
                        "rows": [list(row) for row in table.rows],
                    }
                    result["tables"].append(table_data)

            return result

        except Exception as e:
            raise handle_azure_error(e, resource="Log Analytics Query")
        finally:
            await client.close()

    async def query_logs_resource(
        self,
        resource_id: str,
        query: str,
        timespan: timedelta = timedelta(hours=24),
        include_statistics: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a KQL query directly against an Azure resource.

        This is useful when you don't know the workspace ID but have the resource ID.

        Args:
            resource_id: The full Azure resource ID.
            query: The KQL query to execute.
            timespan: Time range for the query.
            include_statistics: Whether to include query statistics.

        Returns:
            Query results with tables and optional statistics.
        """
        self._check_monitor_query_sdk()
        from azure.monitor.query.aio import LogsQueryClient
        from azure.monitor.query import LogsQueryStatus

        credential = self.get_credential()
        client = LogsQueryClient(credential)

        try:
            response = await client.query_resource(
                resource_id=resource_id,
                query=query,
                timespan=timespan,
                include_statistics=include_statistics,
            )

            result: dict[str, Any] = {"tables": [], "status": "success"}

            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    table_data = {
                        "name": table.name,
                        "columns": [col.name for col in table.columns],
                        "rows": [list(row) for row in table.rows],
                    }
                    result["tables"].append(table_data)

                if include_statistics and response.statistics:
                    result["statistics"] = response.statistics
            elif response.status == LogsQueryStatus.PARTIAL:
                result["status"] = "partial"
                result["error"] = str(response.partial_error)
                for table in response.partial_data:
                    table_data = {
                        "name": table.name,
                        "columns": [col.name for col in table.columns],
                        "rows": [list(row) for row in table.rows],
                    }
                    result["tables"].append(table_data)

            return result

        except Exception as e:
            raise handle_azure_error(e, resource="Resource Log Query")
        finally:
            await client.close()

    async def query_logs_batch(
        self,
        workspace_id: str,
        queries: list[dict[str, Any]],
        timespan: timedelta = timedelta(hours=24),
    ) -> list[dict[str, Any]]:
        """
        Execute multiple KQL queries in a single batch request.

        Args:
            workspace_id: The Log Analytics workspace ID.
            queries: List of query dictionaries with 'id' and 'query' keys.
            timespan: Default time range for queries.

        Returns:
            List of query results, each with 'id' and 'result' keys.
        """
        self._check_monitor_query_sdk()
        from azure.monitor.query.aio import LogsQueryClient
        from azure.monitor.query import LogsBatchQuery, LogsQueryStatus

        credential = self.get_credential()
        client = LogsQueryClient(credential)

        try:
            batch_requests = []
            for q in queries:
                batch_requests.append(
                    LogsBatchQuery(
                        workspace_id=workspace_id,
                        query=q["query"],
                        timespan=q.get("timespan", timespan),
                    )
                )

            responses = await client.query_batch(batch_requests)

            results = []
            for i, response in enumerate(responses):
                query_id = queries[i].get("id", str(i))
                result: dict[str, Any] = {"id": query_id, "tables": []}

                if response.status == LogsQueryStatus.SUCCESS:
                    result["status"] = "success"
                    for table in response.tables:
                        table_data = {
                            "name": table.name,
                            "columns": [col.name for col in table.columns],
                            "rows": [list(row) for row in table.rows],
                        }
                        result["tables"].append(table_data)
                elif response.status == LogsQueryStatus.PARTIAL:
                    result["status"] = "partial"
                    result["error"] = str(response.partial_error)
                    for table in response.partial_data:
                        table_data = {
                            "name": table.name,
                            "columns": [col.name for col in table.columns],
                            "rows": [list(row) for row in table.rows],
                        }
                        result["tables"].append(table_data)
                else:
                    result["status"] = "failed"
                    result["error"] = str(response)

                results.append(result)

            return results

        except Exception as e:
            raise handle_azure_error(e, resource="Batch Log Query")
        finally:
            await client.close()

    # =========================================================================
    # Metrics Queries
    # =========================================================================

    async def query_metrics(
        self,
        resource_id: str,
        metric_names: list[str],
        timespan: timedelta = timedelta(hours=1),
        interval: str = "PT1M",
        aggregations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Query metrics for an Azure resource.

        Args:
            resource_id: The full Azure resource ID.
            metric_names: List of metric names to query.
            timespan: Time range for the query.
            interval: Aggregation interval (ISO 8601 duration, e.g., PT1M, PT5M, PT1H).
            aggregations: List of aggregation types (Average, Total, Maximum, Minimum, Count).

        Returns:
            Metrics data with time series.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        # Extract subscription from resource ID
        parts = resource_id.split("/")
        subscription_idx = parts.index("subscriptions") + 1
        subscription_id = parts[subscription_idx]

        credential = self.get_credential()
        client = MonitorManagementClient(credential, subscription_id)

        try:
            # Build timespan string
            from datetime import datetime, timezone

            end_time = datetime.now(timezone.utc)
            start_time = end_time - timespan
            timespan_str = f"{start_time.isoformat()}/{end_time.isoformat()}"

            response = await client.metrics.list(
                resource_uri=resource_id,
                metricnames=",".join(metric_names),
                timespan=timespan_str,
                interval=interval,
                aggregation=",".join(aggregations) if aggregations else None,
            )

            result = {
                "timespan": timespan_str,
                "interval": interval,
                "metrics": [],
            }

            for metric in response.value:
                metric_data = {
                    "name": metric.name.value if metric.name else "unknown",
                    "unit": metric.unit.value if metric.unit else None,
                    "timeseries": [],
                }

                for ts in metric.timeseries:
                    series_data = {
                        "metadata": {k: v for k, v in (ts.metadatavalues or [])}
                        if ts.metadatavalues
                        else {},
                        "data": [],
                    }

                    for dp in ts.data:
                        data_point = {
                            "timestamp": dp.time_stamp.isoformat() if dp.time_stamp else None,
                        }
                        if dp.average is not None:
                            data_point["average"] = dp.average
                        if dp.total is not None:
                            data_point["total"] = dp.total
                        if dp.maximum is not None:
                            data_point["maximum"] = dp.maximum
                        if dp.minimum is not None:
                            data_point["minimum"] = dp.minimum
                        if dp.count is not None:
                            data_point["count"] = dp.count

                        series_data["data"].append(data_point)

                    metric_data["timeseries"].append(series_data)

                result["metrics"].append(metric_data)

            return result

        except Exception as e:
            raise handle_azure_error(e, resource="Metrics Query")
        finally:
            await client.close()

    async def list_metric_definitions(
        self,
        resource_id: str,
    ) -> list[dict[str, Any]]:
        """
        List available metric definitions for a resource.

        Args:
            resource_id: The full Azure resource ID.

        Returns:
            List of metric definitions with name, unit, and aggregations.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        # Extract subscription from resource ID
        parts = resource_id.split("/")
        subscription_idx = parts.index("subscriptions") + 1
        subscription_id = parts[subscription_idx]

        credential = self.get_credential()
        client = MonitorManagementClient(credential, subscription_id)

        try:
            definitions = []
            async for metric_def in client.metric_definitions.list(resource_id):
                def_data = {
                    "name": metric_def.name.value if metric_def.name else "unknown",
                    "displayName": metric_def.name.localized_value if metric_def.name else None,
                    "unit": metric_def.unit.value if metric_def.unit else None,
                    "primaryAggregationType": (
                        metric_def.primary_aggregation_type.value
                        if metric_def.primary_aggregation_type
                        else None
                    ),
                    "supportedAggregationTypes": [
                        a.value for a in (metric_def.supported_aggregation_types or [])
                    ],
                    "metricAvailabilities": [
                        {
                            "timeGrain": str(ma.time_grain) if ma.time_grain else None,
                            "retention": str(ma.retention) if ma.retention else None,
                        }
                        for ma in (metric_def.metric_availabilities or [])
                    ],
                }
                definitions.append(def_data)

            return definitions

        except Exception as e:
            raise handle_azure_error(e, resource="Metric Definitions")
        finally:
            await client.close()

    async def get_metric_baselines(
        self,
        resource_id: str,
        metric_names: list[str],
        timespan: timedelta = timedelta(hours=24),
        interval: str = "PT1H",
    ) -> list[dict[str, Any]]:
        """
        Get metric baselines for anomaly detection.

        Args:
            resource_id: The full Azure resource ID.
            metric_names: List of metric names.
            timespan: Time range for baseline calculation.
            interval: Aggregation interval.

        Returns:
            List of metric baselines with expected values.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        # Extract subscription from resource ID
        parts = resource_id.split("/")
        subscription_idx = parts.index("subscriptions") + 1
        subscription_id = parts[subscription_idx]

        credential = self.get_credential()
        client = MonitorManagementClient(credential, subscription_id)

        try:
            from datetime import datetime, timezone

            end_time = datetime.now(timezone.utc)
            start_time = end_time - timespan
            timespan_str = f"{start_time.isoformat()}/{end_time.isoformat()}"

            baselines = []
            response = await client.baselines.list(
                resource_uri=resource_id,
                metricnames=",".join(metric_names),
                timespan=timespan_str,
                interval=interval,
            )

            async for baseline in response:
                baseline_data = {
                    "name": baseline.name if baseline.name else "unknown",
                    "type": baseline.type,
                    "baselines": [],
                }

                for ts_baseline in baseline.baselines or []:
                    ts_data = {
                        "aggregation": ts_baseline.aggregation,
                        "timestamps": [t.isoformat() for t in (ts_baseline.timestamps or [])],
                        "data": [],
                    }

                    for bd in ts_baseline.data or []:
                        ts_data["data"].append(
                            {
                                "sensitivity": bd.sensitivity,
                                "lowThresholds": list(bd.low_thresholds)
                                if bd.low_thresholds
                                else [],
                                "highThresholds": list(bd.high_thresholds)
                                if bd.high_thresholds
                                else [],
                            }
                        )

                    baseline_data["baselines"].append(ts_data)

                baselines.append(baseline_data)

            return baselines

        except Exception as e:
            raise handle_azure_error(e, resource="Metric Baselines")
        finally:
            await client.close()

    # =========================================================================
    # Activity Log
    # =========================================================================

    async def query_activity_log(
        self,
        subscription: str,
        resource_group: str = "",
        resource_id: str = "",
        timespan: timedelta = timedelta(days=7),
        operation_name: str = "",
        status: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query Azure Activity Log for resource changes and operations.

        Use this to find out WHO created/deleted/modified Azure resources,
        WHEN changes happened, and WHAT operations were performed.

        For Entra ID (Azure AD) changes like user/group modifications,
        use entraid_audit_logs instead.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            resource_id: Filter by specific resource ID (optional).
            timespan: Time range (default 7 days).
            operation_name: Filter by operation (e.g., "Microsoft.Compute/virtualMachines/write").
            status: Filter by status (Succeeded, Failed, Started, etc.).
            top: Maximum number of events to return.

        Returns:
            List of activity log events.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            from datetime import datetime, timezone

            end_time = datetime.now(timezone.utc)
            start_time = end_time - timespan

            # Build OData filter
            filters = [f"eventTimestamp ge '{start_time.isoformat()}'"]

            if resource_group:
                filters.append(f"resourceGroupName eq '{resource_group}'")
            if resource_id:
                filters.append(f"resourceId eq '{resource_id}'")
            if operation_name:
                filters.append(f"operationName.value eq '{operation_name}'")
            if status:
                filters.append(f"status.value eq '{status}'")

            filter_str = " and ".join(filters)

            events = []
            count = 0
            async for event in client.activity_logs.list(filter=filter_str):
                if count >= top:
                    break

                event_data = {
                    "eventTimestamp": (
                        event.event_timestamp.isoformat() if event.event_timestamp else None
                    ),
                    "operationName": (event.operation_name.value if event.operation_name else None),
                    "operationDisplayName": (
                        event.operation_name.localized_value if event.operation_name else None
                    ),
                    "status": event.status.value if event.status else None,
                    "caller": event.caller,
                    "resourceId": event.resource_id,
                    "resourceGroupName": event.resource_group_name,
                    "resourceType": (event.resource_type.value if event.resource_type else None),
                    "level": event.level.value if event.level else None,
                    "description": event.description,
                    "correlationId": event.correlation_id,
                }

                if event.claims:
                    event_data["claims"] = {
                        "name": event.claims.get("name"),
                        "upn": event.claims.get(
                            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"
                        ),
                        "appid": event.claims.get("appid"),
                    }

                events.append(event_data)
                count += 1

            return events

        except Exception as e:
            raise handle_azure_error(e, resource="Activity Log")
        finally:
            await client.close()

    # =========================================================================
    # Alerts
    # =========================================================================

    async def list_alerts(
        self,
        subscription: str,
        resource_group: str = "",
        severity: str = "",
        state: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List fired alerts in a subscription.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            severity: Filter by severity (Sev0, Sev1, Sev2, Sev3, Sev4).
            state: Filter by state (New, Acknowledged, Closed).
            top: Maximum number of alerts to return.

        Returns:
            List of alert instances.
        """
        # Use Resource Graph for efficient alert listing
        sub_id = await self.resolve_subscription(subscription)

        query = """
        alertsmanagementresources
        | where type == 'microsoft.alertsmanagement/alerts'
        | extend severity = properties.essentials.severity
        | extend alertState = properties.essentials.alertState
        | extend targetResource = properties.essentials.targetResource
        | extend startDateTime = properties.essentials.startDateTime
        | extend monitorCondition = properties.essentials.monitorCondition
        | extend alertRule = properties.essentials.alertRule
        """

        if severity:
            query += f"| where severity == '{severity}'\n"
        if state:
            query += f"| where alertState == '{state}'\n"

        query += f"""
        | project id, name, severity, alertState, targetResource, startDateTime, 
                  monitorCondition, alertRule, resourceGroup
        | order by startDateTime desc
        | take {top}
        """

        try:
            result = await self.execute_resource_graph_query(
                query=query,
                subscriptions=[sub_id],
            )

            alerts = []
            for row in result.get("data", []):
                alerts.append(
                    {
                        "id": row.get("id"),
                        "name": row.get("name"),
                        "severity": row.get("severity"),
                        "state": row.get("alertState"),
                        "targetResource": row.get("targetResource"),
                        "startDateTime": row.get("startDateTime"),
                        "monitorCondition": row.get("monitorCondition"),
                        "alertRule": row.get("alertRule"),
                        "resourceGroup": row.get("resourceGroup"),
                    }
                )

            return alerts

        except Exception as e:
            raise handle_azure_error(e, resource="Alerts")

    async def list_alert_rules(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List configured metric alert rules.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            top: Maximum number of rules to return.

        Returns:
            List of alert rule configurations.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            rules = []
            count = 0

            if resource_group:
                async for rule in client.metric_alerts.list_by_resource_group(resource_group):
                    if count >= top:
                        break
                    rules.append(self._serialize_alert_rule(rule))
                    count += 1
            else:
                async for rule in client.metric_alerts.list_by_subscription():
                    if count >= top:
                        break
                    rules.append(self._serialize_alert_rule(rule))
                    count += 1

            return rules

        except Exception as e:
            raise handle_azure_error(e, resource="Alert Rules")
        finally:
            await client.close()

    def _serialize_alert_rule(self, rule: Any) -> dict[str, Any]:
        """Serialize a metric alert rule to a dictionary."""
        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "enabled": rule.enabled,
            "scopes": list(rule.scopes) if rule.scopes else [],
            "evaluationFrequency": str(rule.evaluation_frequency),
            "windowSize": str(rule.window_size),
            "targetResourceType": rule.target_resource_type,
            "targetResourceRegion": rule.target_resource_region,
            "criteria": self._serialize_criteria(rule.criteria),
            "autoMitigate": rule.auto_mitigate,
        }

    def _serialize_criteria(self, criteria: Any) -> dict[str, Any]:
        """Serialize alert criteria."""
        if not criteria:
            return {}

        result = {"odataType": criteria.odata_type}

        if hasattr(criteria, "all_of") and criteria.all_of:
            result["conditions"] = []
            for condition in criteria.all_of:
                cond_data = {
                    "metricName": condition.metric_name,
                    "metricNamespace": condition.metric_namespace,
                    "operator": condition.operator.value if condition.operator else None,
                    "threshold": condition.threshold,
                    "timeAggregation": (
                        condition.time_aggregation.value if condition.time_aggregation else None
                    ),
                }
                result["conditions"].append(cond_data)

        return result

    async def get_alert_rule(
        self,
        subscription: str,
        resource_group: str,
        rule_name: str,
    ) -> dict[str, Any]:
        """
        Get details of a specific metric alert rule.

        Args:
            subscription: Subscription ID or name.
            resource_group: Resource group containing the rule.
            rule_name: Name of the alert rule.

        Returns:
            Alert rule configuration details.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            rule = await client.metric_alerts.get(resource_group, rule_name)
            if not rule:
                raise AzureResourceError(f"Alert rule '{rule_name}' not found")

            return self._serialize_alert_rule(rule)

        except Exception as e:
            raise handle_azure_error(e, resource=f"Alert Rule '{rule_name}'")
        finally:
            await client.close()

    # =========================================================================
    # Autoscale
    # =========================================================================

    async def list_autoscale_settings(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List autoscale settings.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            top: Maximum number of settings to return.

        Returns:
            List of autoscale configurations.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            settings = []
            count = 0

            if resource_group:
                async for setting in client.autoscale_settings.list_by_resource_group(
                    resource_group
                ):
                    if count >= top:
                        break
                    settings.append(self._serialize_autoscale_setting(setting))
                    count += 1
            else:
                async for setting in client.autoscale_settings.list_by_subscription():
                    if count >= top:
                        break
                    settings.append(self._serialize_autoscale_setting(setting))
                    count += 1

            return settings

        except Exception as e:
            raise handle_azure_error(e, resource="Autoscale Settings")
        finally:
            await client.close()

    def _serialize_autoscale_setting(self, setting: Any) -> dict[str, Any]:
        """Serialize autoscale setting to dictionary."""
        return {
            "id": setting.id,
            "name": setting.name,
            "location": setting.location,
            "targetResourceUri": setting.target_resource_uri,
            "enabled": setting.enabled,
            "profiles": [
                {
                    "name": p.name,
                    "capacity": {
                        "minimum": p.capacity.minimum,
                        "maximum": p.capacity.maximum,
                        "default": p.capacity.default,
                    }
                    if p.capacity
                    else None,
                    "rules": [
                        {
                            "metricName": r.metric_trigger.metric_name
                            if r.metric_trigger
                            else None,
                            "operator": (
                                r.metric_trigger.operator.value
                                if r.metric_trigger and r.metric_trigger.operator
                                else None
                            ),
                            "threshold": r.metric_trigger.threshold if r.metric_trigger else None,
                            "direction": (
                                r.scale_action.direction.value
                                if r.scale_action and r.scale_action.direction
                                else None
                            ),
                            "changeCount": r.scale_action.value if r.scale_action else None,
                        }
                        for r in (p.rules or [])
                    ],
                }
                for p in (setting.profiles or [])
            ],
        }

    async def get_autoscale_setting(
        self,
        subscription: str,
        resource_group: str,
        setting_name: str,
    ) -> dict[str, Any]:
        """
        Get details of a specific autoscale setting.

        Args:
            subscription: Subscription ID or name.
            resource_group: Resource group containing the setting.
            setting_name: Name of the autoscale setting.

        Returns:
            Autoscale configuration details.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            setting = await client.autoscale_settings.get(resource_group, setting_name)
            if not setting:
                raise AzureResourceError(f"Autoscale setting '{setting_name}' not found")

            return self._serialize_autoscale_setting(setting)

        except Exception as e:
            raise handle_azure_error(e, resource=f"Autoscale Setting '{setting_name}'")
        finally:
            await client.close()

    # =========================================================================
    # Configuration - Workspaces, Action Groups, Diagnostics, etc.
    # =========================================================================

    async def list_workspaces(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List Log Analytics workspaces.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            top: Maximum number of workspaces to return.

        Returns:
            List of workspace details.
        """
        sub_id = await self.resolve_subscription(subscription)

        # Use Resource Graph for efficient listing
        query = """
        resources
        | where type == 'microsoft.operationalinsights/workspaces'
        """

        if resource_group:
            query += f"| where resourceGroup =~ '{resource_group}'\n"

        query += f"""
        | project id, name, resourceGroup, location, 
                  customerId = properties.customerId,
                  sku = properties.sku.name,
                  retentionInDays = properties.retentionInDays,
                  provisioningState = properties.provisioningState
        | take {top}
        """

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
        )

        return result.get("data", [])

    async def list_action_groups(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List notification action groups.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            top: Maximum number of groups to return.

        Returns:
            List of action group configurations.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            groups = []
            count = 0

            if resource_group:
                async for group in client.action_groups.list_by_resource_group(resource_group):
                    if count >= top:
                        break
                    groups.append(self._serialize_action_group(group))
                    count += 1
            else:
                async for group in client.action_groups.list_by_subscription_id():
                    if count >= top:
                        break
                    groups.append(self._serialize_action_group(group))
                    count += 1

            return groups

        except Exception as e:
            raise handle_azure_error(e, resource="Action Groups")
        finally:
            await client.close()

    def _serialize_action_group(self, group: Any) -> dict[str, Any]:
        """Serialize action group to dictionary."""
        return {
            "id": group.id,
            "name": group.name,
            "location": group.location,
            "enabled": group.enabled,
            "shortName": group.group_short_name,
            "emailReceivers": [
                {
                    "name": r.name,
                    "email": r.email_address,
                    "status": r.status.value if r.status else None,
                }
                for r in (group.email_receivers or [])
            ],
            "smsReceivers": [
                {
                    "name": r.name,
                    "phoneNumber": r.phone_number,
                    "status": r.status.value if r.status else None,
                }
                for r in (group.sms_receivers or [])
            ],
            "webhookReceivers": [
                {"name": r.name, "serviceUri": r.service_uri}
                for r in (group.webhook_receivers or [])
            ],
            "azureAppPushReceivers": [
                {"name": r.name, "email": r.email_address}
                for r in (group.azure_app_push_receivers or [])
            ],
        }

    async def list_diagnostic_settings(
        self,
        resource_id: str,
    ) -> list[dict[str, Any]]:
        """
        List diagnostic settings for a resource.

        Args:
            resource_id: The full Azure resource ID.

        Returns:
            List of diagnostic setting configurations.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        # Extract subscription from resource ID
        parts = resource_id.split("/")
        subscription_idx = parts.index("subscriptions") + 1
        subscription_id = parts[subscription_idx]

        credential = self.get_credential()
        client = MonitorManagementClient(credential, subscription_id)

        try:
            settings = []
            result = await client.diagnostic_settings.list(resource_id)

            for setting in result.value or []:
                setting_data = {
                    "id": setting.id,
                    "name": setting.name,
                    "storageAccountId": setting.storage_account_id,
                    "workspaceId": setting.workspace_id,
                    "eventHubAuthorizationRuleId": setting.event_hub_authorization_rule_id,
                    "eventHubName": setting.event_hub_name,
                    "logs": [
                        {
                            "category": log.category,
                            "categoryGroup": log.category_group,
                            "enabled": log.enabled,
                        }
                        for log in (setting.logs or [])
                    ],
                    "metrics": [
                        {
                            "category": m.category,
                            "enabled": m.enabled,
                            "timeGrain": str(m.time_grain) if m.time_grain else None,
                        }
                        for m in (setting.metrics or [])
                    ],
                }
                settings.append(setting_data)

            return settings

        except Exception as e:
            raise handle_azure_error(e, resource="Diagnostic Settings")
        finally:
            await client.close()

    async def list_data_collection_rules(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List data collection rules.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            top: Maximum number of rules to return.

        Returns:
            List of data collection rule configurations.
        """
        sub_id = await self.resolve_subscription(subscription)

        # Use Resource Graph for efficient listing
        query = """
        resources
        | where type == 'microsoft.insights/datacollectionrules'
        """

        if resource_group:
            query += f"| where resourceGroup =~ '{resource_group}'\n"

        query += f"""
        | project id, name, resourceGroup, location,
                  kind = properties.kind,
                  description = properties.description,
                  dataSources = properties.dataSources,
                  destinations = properties.destinations
        | take {top}
        """

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
        )

        return result.get("data", [])

    async def list_scheduled_query_rules(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List scheduled query (log-based) alert rules.

        Args:
            subscription: Subscription ID or name.
            resource_group: Filter by resource group (optional).
            top: Maximum number of rules to return.

        Returns:
            List of scheduled query rule configurations.
        """
        self._check_monitor_mgmt_sdk()
        from azure.mgmt.monitor.aio import MonitorManagementClient

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()
        client = MonitorManagementClient(credential, sub_id)

        try:
            rules = []
            count = 0

            if resource_group:
                async for rule in client.scheduled_query_rules.list_by_resource_group(
                    resource_group
                ):
                    if count >= top:
                        break
                    rules.append(self._serialize_scheduled_query_rule(rule))
                    count += 1
            else:
                async for rule in client.scheduled_query_rules.list_by_subscription():
                    if count >= top:
                        break
                    rules.append(self._serialize_scheduled_query_rule(rule))
                    count += 1

            return rules

        except Exception as e:
            raise handle_azure_error(e, resource="Scheduled Query Rules")
        finally:
            await client.close()

    def _serialize_scheduled_query_rule(self, rule: Any) -> dict[str, Any]:
        """Serialize scheduled query rule to dictionary."""
        return {
            "id": rule.id,
            "name": rule.name,
            "location": rule.location,
            "description": rule.description,
            "severity": rule.severity,
            "enabled": rule.enabled,
            "scopes": list(rule.scopes) if rule.scopes else [],
            "evaluationFrequency": str(rule.evaluation_frequency)
            if rule.evaluation_frequency
            else None,
            "windowSize": str(rule.window_size) if rule.window_size else None,
            "criteria": {
                "allOf": [
                    {
                        "query": c.query,
                        "operator": c.operator.value if c.operator else None,
                        "threshold": c.threshold,
                        "timeAggregation": c.time_aggregation.value if c.time_aggregation else None,
                    }
                    for c in (rule.criteria.all_of if rule.criteria else [])
                ]
            }
            if rule.criteria
            else None,
        }
