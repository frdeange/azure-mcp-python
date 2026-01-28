# COPY INSTRUCTIONS

This folder contains the complete Azure MCP Server Python project, including:
- Complete core framework implementation
- First tool (resourcegraph_query)
- Full test suite structure
- GitHub workflows and issue templates
- **50+ planned issues** ready to import
- **Research notes** from .NET project analysis
- **Project plan** with milestones and decisions

## To copy to your host machine:

### Option 1: VS Code Download
1. In VS Code, right-click on the `_azure-mcp-python` folder
2. Select "Download..." 
3. Save to `c:\repos\azure-mcp-python`

### Option 2: Docker Copy
```bash
# From Windows PowerShell (outside the Dev Container)
docker cp <container_id>:/workspaces/Azure.Mcp.Server/_azure-mcp-python c:\repos\azure-mcp-python
```

### Option 3: Git (if already pushed)
```bash
git clone https://github.com/YOUR_USER/azure-mcp-python.git
```

## After copying:

1. Open the new folder in VS Code
2. Open in Dev Container (or create a Python virtual environment)
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Run tests:
   ```bash
   pytest tests/unit -v
   ```
5. Initialize git:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Core framework and Resource Graph tool"
   ```

## Project Structure Summary

```
azure-mcp-python/
├── .devcontainer/           # Dev Container config
├── .github/                 # GitHub templates & workflows
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   ├── workflows/           # CI/CD workflows
│   └── pull_request_template.md
├── docs/                    # Documentation
│   ├── adding-tools.md      # How to add new tools
│   ├── authentication.md    # Auth guide
│   └── testing.md           # Testing guide
├── src/azure_mcp/           # Main package
│   ├── core/                # Core framework
│   │   ├── auth.py          # Credential management
│   │   ├── base.py          # AzureService & AzureTool
│   │   ├── cache.py         # Caching service
│   │   ├── errors.py        # Error types
│   │   ├── models.py        # Data models
│   │   └── registry.py      # Tool registry
│   ├── tools/               # Tool implementations
│   │   └── resourcegraph/   # First tool
│   └── server.py            # MCP entry point
├── tests/                   # Test suite
│   ├── unit/
│   └── integration/
├── pyproject.toml           # Project configuration
├── README.md                # Main documentation
├── ARCHITECTURE.md          # Architecture design
├── CONTRIBUTING.md          # Contribution guide
└── CHANGELOG.md             # Version history
```

## Documentation Included

All planning and research is preserved in the `.github/` folder:

| File | Content |
|------|---------|
| [.github/PROJECT_PLAN.md](.github/PROJECT_PLAN.md) | Executive summary, architecture decisions, milestones |
| [.github/ISSUES.md](.github/ISSUES.md) | 50+ planned issues with full descriptions |
| [.github/RESEARCH_NOTES.md](.github/RESEARCH_NOTES.md) | .NET analysis, Python SDK research, comparisons |
| [scripts/create-github-issues.sh](scripts/create-github-issues.sh) | Script to auto-create issues in GitHub |

## Create GitHub Issues

After pushing to GitHub, run the script to create all issues:

```bash
chmod +x scripts/create-github-issues.sh
./scripts/create-github-issues.sh
```

This will create:
- Labels (core, tool, priority, etc.)
- Milestones (7 milestones)
- Issues (Cost Management, Entra ID, Storage, Cosmos, etc.)

## Next Steps

| Priority | Milestone | Status |
|----------|-----------|--------|
| ✅ | 1. Core Framework | COMPLETE |
| ✅ | Resource Graph tool | COMPLETE |
| ⭐ | 4. Cost Management | PRIORITY - Start here! |
| ⭐ | 5. Entra ID | PRIORITY |
| 🔄 | 2. Storage Tools | Next |
| 🔄 | 3. Cosmos DB Tools | Next |
| ⏳ | 6. Key Vault | Later |
| ⏳ | 7. Additional Services | Later |

## Quick Start for Adding Tools

See [docs/adding-tools.md](docs/adding-tools.md) for the complete guide.

Quick example:

```python
@register_tool("cost", "query")
class CostQueryTool(AzureTool):
    @property
    def name(self) -> str:
        return "cost_query"
    
    # ... implement the rest
```
