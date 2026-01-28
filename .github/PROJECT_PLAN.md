# Azure MCP Server - Python Migration Plan

## Executive Summary

This project is a migration of the Azure MCP Server from .NET to Python, driven by:

1. **Team expertise** - Team is more comfortable with Python
2. **Extension velocity** - Microsoft's development pace doesn't match our needs
3. **Custom tools** - Need to add Cost Management, Entra ID, and other tools not in the .NET version
4. **Maintenance cost** - Python offers lower maintenance overhead for our team

## Research Findings

### Original .NET Project Analysis

The original project at `AzureMCPServer/` contains:

- **45+ tool implementations** across Azure services
- **Modular architecture** with separate projects per service family
- **Core framework** providing:
  - Azure Resource Graph integration for resource discovery
  - Credential management with multi-tenant support
  - Tool registration and schema generation
  - Error handling with Azure-specific error types

### Key .NET Patterns to Preserve

1. **Resource Graph as Primary Discovery**
   - All `list_*` operations use ARG queries, not individual API calls
   - Dramatically reduces API calls and improves performance
   - Enables cross-subscription queries

2. **Tool Metadata System**
   - `readOnly`, `requiresConfirmation`, `idempotent` flags
   - Helps LLMs make safer decisions about tool usage

3. **Hierarchical Tool Organization**
   - Tools grouped by service family
   - Consistent naming: `{family}_{resource}_{action}`

### Python MCP SDK Compatibility

The official Python MCP SDK (`mcp` package) provides:

- Full MCP protocol 2024-11-05 support
- FastMCP for rapid tool development
- Async-first design (matches Azure SDK for Python)
- JSON Schema generation from Pydantic models

### Azure SDK for Python Mapping

| .NET Package | Python Package | Status |
|--------------|----------------|--------|
| Azure.Identity | azure-identity | ✅ Full parity |
| Azure.ResourceManager | azure-mgmt-resource | ✅ Full parity |
| Azure.ResourceManager.ResourceGraph | azure-mgmt-resourcegraph | ✅ Full parity |
| Azure.Storage.Blobs | azure-storage-blob | ✅ Full parity |
| Azure.Data.Tables | azure-data-tables | ✅ Full parity |
| Azure.Cosmos | azure-cosmos | ✅ Full parity |
| Microsoft.Graph | msgraph-sdk | ✅ Full parity |
| Azure.CostManagement | azure-mgmt-costmanagement | ✅ Available |

## Architecture Decisions

### AD-001: Use `src/` Layout

**Decision**: Use `src/azure_mcp/` layout instead of flat `azure_mcp/`

**Rationale**:
- PyPA recommended best practice
- Prevents import confusion during development
- Cleaner separation of source and tests

### AD-002: Pydantic for Input Validation

**Decision**: Use Pydantic models for all tool options

**Rationale**:
- Automatic JSON Schema generation for MCP
- Rich validation with helpful error messages
- IDE support with type hints
- Standard in modern Python projects

### AD-003: Resource Graph in Core

**Decision**: Include Resource Graph helpers in `AzureService` base class

**Rationale**:
- Most tools need resource listing/discovery
- Avoids code duplication across tools
- Consistent pattern for all services

### AD-004: Optional Dependencies per Service

**Decision**: Use optional dependency groups in `pyproject.toml`

**Rationale**:
- Minimizes base install size
- Users install only needed Azure SDKs
- Example: `pip install azure-mcp-server[cosmos,storage]`

### AD-005: Singleton Tool Registry

**Decision**: Global registry with `@register_tool` decorator

**Rationale**:
- Tools self-register on import
- Simple discovery mechanism
- Matches MCP server initialization pattern

## Milestones

### Milestone 1: Core Framework (Week 1-2)
Foundation for all tools.

### Milestone 2: Storage Tools (Week 2-3)
Blob, Queue, Table, File Share operations.

### Milestone 3: Cosmos DB Tools (Week 3-4)
Container and item operations.

### Milestone 4: Cost Management Tools (Week 4-5) ⭐ PRIORITY
New functionality not in .NET version.

### Milestone 5: Entra ID Tools (Week 5-6) ⭐ PRIORITY
New functionality not in .NET version.

### Milestone 6: Key Vault Tools (Week 6-7)
Secrets, keys, certificates.

### Milestone 7: Additional Services (Week 7+)
Event Grid, Service Bus, Functions, etc.

## Success Criteria

1. **Feature Parity** - Cover most common .NET tools
2. **New Features** - Cost Management and Entra ID tools
3. **Documentation** - Comprehensive guides for adding tools
4. **Test Coverage** - 85%+ coverage
5. **Performance** - Response times within 10% of .NET version

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Azure SDK differences | Medium | Document Python-specific patterns |
| MCP protocol changes | Low | Pin MCP SDK version |
| Performance gaps | Medium | Async throughout, caching |
| Missing SDK features | Low | Fall back to REST API |

## Team Responsibilities

- **Core Framework**: Initial implementation complete
- **Tool Development**: Follow `docs/adding-tools.md` guide
- **Testing**: Unit tests for each tool
- **Documentation**: Update README and docs for each new tool
