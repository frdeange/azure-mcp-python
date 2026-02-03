# Contributing Guide

Thank you for your interest in contributing to Azure MCP Server!

## Development Setup

### Prerequisites

- Python 3.12+
- Azure CLI (`az login` for authentication)
- Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/your-org/azure-mcp-python.git
cd azure-mcp-python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install
```

### Using DevContainer

Open the repository in VS Code and click "Reopen in Container" when prompted.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=azure_mcp

# Run specific test file
pytest tests/unit/core/test_auth.py
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check code
ruff check src tests

# Format code
ruff format src tests

# Type checking
mypy src
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main` (`git checkout -b feature/my-feature`)
3. **Make your changes** with tests
4. **Run checks** (`ruff check && pytest`)
5. **Commit** with descriptive message
6. **Push** and create a Pull Request

### Commit Message Format

Use conventional commits:

```
feat: add cosmos item create tool
fix: handle empty subscription list
docs: update authentication guide
test: add keyvault secret tests
```

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`ruff format`)
- [ ] No lint errors (`ruff check`)
- [ ] Type hints are correct (`mypy`)
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated

## Adding a New Tool

See [docs/adding-tools.md](docs/adding-tools.md) for the complete guide.

### Quick Summary

1. Create tool file in `src/azure_mcp/tools/{family}/`
2. Define Pydantic options model
3. Implement tool class extending `AzureTool`
4. Add `@register_tool` decorator
5. Add tests in `tests/unit/tools/{family}/`
6. Update docs in `docs/tools/{family}.md`

## Issue Labels

| Label | Description |
|-------|-------------|
| `tool:new` | New tool implementation |
| `tool:enhancement` | Improvement to existing tool |
| `core` | Core framework changes |
| `docs` | Documentation only |
| `bug` | Something isn't working |
| `good first issue` | Good for newcomers |

## Questions?

Open a Discussion or reach out to the maintainers.
