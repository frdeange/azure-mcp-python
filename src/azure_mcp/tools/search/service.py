"""Azure AI Search service layer.

Provides SearchService for Azure AI Search operations using native async SDK.
Uses AAD authentication only (DefaultAzureCredential) for security.

Architecture: Uses async SDK clients (.aio modules) for non-blocking I/O.
- azure.search.documents.aio.SearchClient for document operations
- azure.search.documents.indexes.aio.SearchIndexClient for index management
"""

from __future__ import annotations

from typing import Any

from azure_mcp.core.base import AzureService


class SearchService(AzureService):
    """
    Service for Azure AI Search operations.

    Uses azure-search-documents async SDK (.aio modules) with AAD authentication.
    Service discovery uses Resource Graph (base class methods).

    Architecture Note:
        All Search SDK clients have async versions available:
        - azure.search.documents.aio.SearchClient
        - azure.search.documents.indexes.aio.SearchIndexClient

        Using async clients prevents blocking the event loop during
        search operations which may involve network latency.
    """

    # -------------------------------------------------------------------------
    # Resource Discovery (via Resource Graph)
    # -------------------------------------------------------------------------

    async def list_search_services(
        self,
        subscription: str,
        resource_group: str = "",
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List Azure AI Search services using Resource Graph.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            top: Maximum number of results.

        Returns:
            List of search services with endpoints and details.
        """
        sub_id = await self.resolve_subscription(subscription)

        query = (
            "resources"
            " | where type =~ 'microsoft.search/searchservices'"
            " | project name, id, resourceGroup, location, subscriptionId,"
            " sku = sku.name,"
            " endpoint = strcat('https://', name, '.search.windows.net'),"
            " replicaCount = properties.replicaCount,"
            " partitionCount = properties.partitionCount,"
            " hostingMode = properties.hostingMode,"
            " publicNetworkAccess = properties.publicNetworkAccess,"
            " status = properties.status,"
            " provisioningState = properties.provisioningState"
        )

        if resource_group:
            escaped_rg = self._escape_kql(resource_group)
            query += f" | where resourceGroup =~ '{escaped_rg}'"

        query += f" | order by name | take {top}"

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
            top=top,
        )
        return result.get("data", [])

    async def get_search_service(
        self,
        subscription: str,
        service_name: str,
        resource_group: str = "",
    ) -> dict[str, Any] | None:
        """
        Get a specific Azure AI Search service.

        Args:
            subscription: Subscription ID or name.
            service_name: Name of the search service.
            resource_group: Optional resource group filter.

        Returns:
            Service details with endpoint, or None if not found.
        """
        sub_id = await self.resolve_subscription(subscription)
        escaped_name = self._escape_kql(service_name)

        query = (
            "resources"
            " | where type =~ 'microsoft.search/searchservices'"
            f" | where name =~ '{escaped_name}'"
        )

        if resource_group:
            escaped_rg = self._escape_kql(resource_group)
            query += f" | where resourceGroup =~ '{escaped_rg}'"

        query += (
            " | project name, id, resourceGroup, location, subscriptionId,"
            " sku = sku.name,"
            " endpoint = strcat('https://', name, '.search.windows.net'),"
            " replicaCount = properties.replicaCount,"
            " partitionCount = properties.partitionCount,"
            " hostingMode = properties.hostingMode,"
            " publicNetworkAccess = properties.publicNetworkAccess,"
            " status = properties.status,"
            " provisioningState = properties.provisioningState,"
            " networkRuleSet = properties.networkRuleSet,"
            " encryptionWithCmk = properties.encryptionWithCmk,"
            " disableLocalAuth = properties.disableLocalAuth,"
            " authOptions = properties.authOptions"
        )

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
            top=1,
        )
        data = result.get("data", [])
        return data[0] if data else None

    # -------------------------------------------------------------------------
    # Index Management (async)
    # -------------------------------------------------------------------------

    async def list_indexes(
        self,
        endpoint: str,
    ) -> list[dict[str, Any]]:
        """
        List all indexes in a search service.

        Args:
            endpoint: Search service endpoint (e.g., https://myservice.search.windows.net).

        Returns:
            List of index names and basic information.
        """
        from azure.search.documents.indexes.aio import SearchIndexClient

        credential = self.get_credential()

        async with SearchIndexClient(endpoint=endpoint, credential=credential) as client:
            indexes = []
            async for index in client.list_indexes():
                indexes.append(
                    {
                        "name": index.name,
                        "fields_count": len(index.fields) if index.fields else 0,
                        "suggesters_count": len(index.suggesters) if index.suggesters else 0,
                        "scoring_profiles_count": (
                            len(index.scoring_profiles) if index.scoring_profiles else 0
                        ),
                        "analyzers_count": len(index.analyzers) if index.analyzers else 0,
                        "semantic_search": index.semantic_search is not None,
                        "vector_search": index.vector_search is not None,
                    }
                )
            return indexes

    async def get_index(
        self,
        endpoint: str,
        index_name: str,
    ) -> dict[str, Any]:
        """
        Get detailed index definition including schema and fields.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.

        Returns:
            Index definition with fields, analyzers, scoring profiles, etc.
        """
        from azure.search.documents.indexes.aio import SearchIndexClient

        credential = self.get_credential()

        async with SearchIndexClient(endpoint=endpoint, credential=credential) as client:
            index = await client.get_index(index_name)

            # Convert fields to dictionaries
            fields = []
            for field in index.fields or []:
                field_dict: dict[str, Any] = {
                    "name": field.name,
                    "type": str(field.type),
                    "searchable": getattr(field, "searchable", None),
                    "filterable": getattr(field, "filterable", None),
                    "sortable": getattr(field, "sortable", None),
                    "facetable": getattr(field, "facetable", None),
                    "key": getattr(field, "key", None),
                    "retrievable": getattr(field, "retrievable", None) or not getattr(field, "hidden", False),
                }
                if field.analyzer_name:
                    field_dict["analyzer"] = field.analyzer_name
                if field.search_analyzer_name:
                    field_dict["search_analyzer"] = field.search_analyzer_name
                if field.index_analyzer_name:
                    field_dict["index_analyzer"] = field.index_analyzer_name
                if hasattr(field, "vector_search_dimensions") and field.vector_search_dimensions:
                    field_dict["vector_search_dimensions"] = field.vector_search_dimensions
                if (
                    hasattr(field, "vector_search_profile_name")
                    and field.vector_search_profile_name
                ):
                    field_dict["vector_search_profile"] = field.vector_search_profile_name
                fields.append(field_dict)

            # Convert suggesters
            suggesters = []
            for suggester in index.suggesters or []:
                suggesters.append(
                    {
                        "name": suggester.name,
                        "source_fields": list(suggester.source_fields or []),
                    }
                )

            # Convert scoring profiles
            scoring_profiles = []
            for profile in index.scoring_profiles or []:
                scoring_profiles.append(
                    {
                        "name": profile.name,
                        "text_weights": (
                            dict(profile.text_weights.weights) if profile.text_weights else None
                        ),
                        "functions_count": len(profile.functions) if profile.functions else 0,
                    }
                )

            result: dict[str, Any] = {
                "name": index.name,
                "fields": fields,
                "suggesters": suggesters,
                "scoring_profiles": scoring_profiles,
                "default_scoring_profile": index.default_scoring_profile,
                "cors_options": (
                    {
                        "allowed_origins": list(index.cors_options.allowed_origins or []),
                        "max_age_in_seconds": index.cors_options.max_age_in_seconds,
                    }
                    if index.cors_options
                    else None
                ),
            }

            # Add semantic search config if present
            if index.semantic_search:
                result["semantic_search"] = {
                    "default_configuration_name": index.semantic_search.default_configuration_name,
                    "configurations_count": (
                        len(index.semantic_search.configurations)
                        if index.semantic_search.configurations
                        else 0
                    ),
                }

            # Add vector search config if present
            if index.vector_search:
                result["vector_search"] = {
                    "algorithms_count": (
                        len(index.vector_search.algorithms) if index.vector_search.algorithms else 0
                    ),
                    "profiles_count": (
                        len(index.vector_search.profiles) if index.vector_search.profiles else 0
                    ),
                    "vectorizers_count": (
                        len(index.vector_search.vectorizers)
                        if index.vector_search.vectorizers
                        else 0
                    ),
                }

            return result

    async def get_index_statistics(
        self,
        endpoint: str,
        index_name: str,
    ) -> dict[str, Any]:
        """
        Get index statistics including document count and storage size.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.

        Returns:
            Index statistics with document count and storage size.
        """
        from azure.search.documents.indexes.aio import SearchIndexClient

        credential = self.get_credential()

        async with SearchIndexClient(endpoint=endpoint, credential=credential) as client:
            stats = await client.get_index_statistics(index_name)
            return {
                "document_count": stats.document_count,
                "storage_size_bytes": stats.storage_size,
                "storage_size_mb": round(stats.storage_size / (1024 * 1024), 2),
                "vector_index_size_bytes": getattr(stats, "vector_index_size", None),
            }

    # -------------------------------------------------------------------------
    # Search Operations (async)
    # -------------------------------------------------------------------------

    async def search_documents(
        self,
        endpoint: str,
        index_name: str,
        search_text: str = "*",
        filter_expression: str = "",
        select_fields: str = "",
        order_by: str = "",
        top: int = 50,
        skip: int = 0,
        include_total_count: bool = False,
        search_fields: str = "",
        highlight_fields: str = "",
        facets: list[str] | None = None,
        query_type: str = "simple",
        search_mode: str = "any",
    ) -> dict[str, Any]:
        """
        Execute a search query against an index.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index to search.
            search_text: Search query text. Use '*' for all documents.
            filter_expression: OData filter expression.
            select_fields: Comma-separated fields to return.
            order_by: Comma-separated fields to sort by (e.g., 'rating desc, price asc').
            top: Maximum documents to return.
            skip: Number of results to skip for pagination.
            include_total_count: Include total count of matching documents.
            search_fields: Comma-separated fields to search in.
            highlight_fields: Comma-separated fields to highlight.
            facets: List of fields to facet on.
            query_type: Query type ('simple' or 'full' for Lucene syntax).
            search_mode: Search mode ('any' or 'all' for term matching).

        Returns:
            Search results with documents, facets, and optional count.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            # Build search parameters
            search_params: dict[str, Any] = {
                "search_text": search_text if search_text != "*" else None,
                "top": top,
                "skip": skip,
                "include_total_count": include_total_count,
            }

            if filter_expression:
                search_params["filter"] = filter_expression
            if select_fields:
                search_params["select"] = [f.strip() for f in select_fields.split(",")]
            if order_by:
                search_params["order_by"] = [f.strip() for f in order_by.split(",")]
            if search_fields:
                search_params["search_fields"] = [f.strip() for f in search_fields.split(",")]
            if highlight_fields:
                search_params["highlight_fields"] = highlight_fields
            if facets:
                search_params["facets"] = facets
            if query_type:
                search_params["query_type"] = query_type
            if search_mode:
                search_params["search_mode"] = search_mode

            results = await client.search(**search_params)

            # Collect documents
            documents = []
            async for result in results:
                doc = dict(result)
                # Add search metadata if present
                if "@search.score" in doc:
                    doc["_search_score"] = doc.pop("@search.score")
                if "@search.highlights" in doc:
                    doc["_highlights"] = doc.pop("@search.highlights")
                documents.append(doc)

            response: dict[str, Any] = {
                "documents": documents,
                "count": len(documents),
            }

            # Add total count if requested
            if include_total_count:
                response["total_count"] = await results.get_count()

            # Add facets if present
            facet_results = await results.get_facets()
            if facet_results:
                response["facets"] = {
                    name: [{"value": f.value, "count": f.count} for f in facet_list]
                    for name, facet_list in facet_results.items()
                }

            return response

    async def get_document(
        self,
        endpoint: str,
        index_name: str,
        key: str,
        selected_fields: str = "",
    ) -> dict[str, Any]:
        """
        Get a specific document by its key.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.
            key: The document key (value of the key field).
            selected_fields: Comma-separated fields to return.

        Returns:
            The document or raises an error if not found.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            selected = [f.strip() for f in selected_fields.split(",")] if selected_fields else None
            document = await client.get_document(key=key, selected_fields=selected)
            return dict(document)

    # -------------------------------------------------------------------------
    # Suggestions and Autocomplete (async)
    # -------------------------------------------------------------------------

    async def suggest(
        self,
        endpoint: str,
        index_name: str,
        search_text: str,
        suggester_name: str,
        filter_expression: str = "",
        select_fields: str = "",
        top: int = 5,
        use_fuzzy_matching: bool = False,
        highlight_pre_tag: str = "",
        highlight_post_tag: str = "",
    ) -> list[dict[str, Any]]:
        """
        Get search suggestions based on partial query text.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.
            search_text: Partial search text for suggestions.
            suggester_name: Name of the suggester configured in the index.
            filter_expression: OData filter to narrow suggestions.
            select_fields: Comma-separated fields to return with suggestions.
            top: Maximum suggestions to return.
            use_fuzzy_matching: Enable fuzzy matching for typo tolerance.
            highlight_pre_tag: Tag to insert before highlighted text.
            highlight_post_tag: Tag to insert after highlighted text.

        Returns:
            List of suggestions with text and optional document fields.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            suggest_params: dict[str, Any] = {
                "search_text": search_text,
                "suggester_name": suggester_name,
                "top": top,
                "use_fuzzy_matching": use_fuzzy_matching,
            }

            if filter_expression:
                suggest_params["filter"] = filter_expression
            if select_fields:
                suggest_params["select"] = [f.strip() for f in select_fields.split(",")]
            if highlight_pre_tag:
                suggest_params["highlight_pre_tag"] = highlight_pre_tag
            if highlight_post_tag:
                suggest_params["highlight_post_tag"] = highlight_post_tag

            results = await client.suggest(**suggest_params)

            suggestions = []
            async for suggestion in results:
                suggestions.append(
                    {
                        "text": suggestion.text,
                        "document": {k: v for k, v in suggestion.items() if k != "text"},
                    }
                )

            return suggestions

    async def autocomplete(
        self,
        endpoint: str,
        index_name: str,
        search_text: str,
        suggester_name: str,
        mode: str = "oneTerm",
        filter_expression: str = "",
        top: int = 5,
        use_fuzzy_matching: bool = False,
        highlight_pre_tag: str = "",
        highlight_post_tag: str = "",
    ) -> list[dict[str, Any]]:
        """
        Get autocomplete suggestions for partial terms.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.
            search_text: Partial search text for autocomplete.
            suggester_name: Name of the suggester configured in the index.
            mode: Autocomplete mode ('oneTerm', 'twoTerms', 'oneTermWithContext').
            filter_expression: OData filter to narrow results.
            top: Maximum completions to return.
            use_fuzzy_matching: Enable fuzzy matching for typo tolerance.
            highlight_pre_tag: Tag to insert before highlighted text.
            highlight_post_tag: Tag to insert after highlighted text.

        Returns:
            List of autocomplete suggestions with text and query text.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            autocomplete_params: dict[str, Any] = {
                "search_text": search_text,
                "suggester_name": suggester_name,
                "mode": mode,
                "top": top,
                "use_fuzzy_matching": use_fuzzy_matching,
            }

            if filter_expression:
                autocomplete_params["filter"] = filter_expression
            if highlight_pre_tag:
                autocomplete_params["highlight_pre_tag"] = highlight_pre_tag
            if highlight_post_tag:
                autocomplete_params["highlight_post_tag"] = highlight_post_tag

            results = await client.autocomplete(**autocomplete_params)

            completions = []
            async for completion in results:
                completions.append(
                    {
                        "text": completion.text,
                        "query_plus_text": completion.query_plus_text,
                    }
                )

            return completions

    # -------------------------------------------------------------------------
    # Document Management (async)
    # -------------------------------------------------------------------------

    async def upload_documents(
        self,
        endpoint: str,
        index_name: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Upload documents to an index. New documents are added, existing are replaced.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.
            documents: List of documents to upload. Each must include the key field.

        Returns:
            Upload results with success/failure counts.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            result = await client.upload_documents(documents=documents)

            succeeded = sum(1 for r in result if r.succeeded)
            failed = sum(1 for r in result if not r.succeeded)

            response: dict[str, Any] = {
                "total": len(result),
                "succeeded": succeeded,
                "failed": failed,
            }

            if failed > 0:
                response["errors"] = [
                    {
                        "key": r.key,
                        "error_message": r.error_message,
                        "status_code": r.status_code,
                    }
                    for r in result
                    if not r.succeeded
                ]

            return response

    async def merge_documents(
        self,
        endpoint: str,
        index_name: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Merge documents into existing documents. Only specified fields are updated.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.
            documents: List of partial documents to merge. Each must include the key field.

        Returns:
            Merge results with success/failure counts.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            result = await client.merge_documents(documents=documents)

            succeeded = sum(1 for r in result if r.succeeded)
            failed = sum(1 for r in result if not r.succeeded)

            response: dict[str, Any] = {
                "total": len(result),
                "succeeded": succeeded,
                "failed": failed,
            }

            if failed > 0:
                response["errors"] = [
                    {
                        "key": r.key,
                        "error_message": r.error_message,
                        "status_code": r.status_code,
                    }
                    for r in result
                    if not r.succeeded
                ]

            return response

    async def delete_documents(
        self,
        endpoint: str,
        index_name: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Delete documents from an index by their keys.

        Args:
            endpoint: Search service endpoint.
            index_name: Name of the index.
            documents: List of documents containing at least the key field.

        Returns:
            Delete results with success/failure counts.
        """
        from azure.search.documents.aio import SearchClient

        credential = self.get_credential()

        async with SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        ) as client:
            result = await client.delete_documents(documents=documents)

            succeeded = sum(1 for r in result if r.succeeded)
            failed = sum(1 for r in result if not r.succeeded)

            response: dict[str, Any] = {
                "total": len(result),
                "succeeded": succeeded,
                "failed": failed,
            }

            if failed > 0:
                response["errors"] = [
                    {
                        "key": r.key,
                        "error_message": r.error_message,
                        "status_code": r.status_code,
                    }
                    for r in result
                    if not r.succeeded
                ]

            return response
