# Agent Instructions for agentic-crew

## Overview

`agentic-crew` is a **framework-agnostic AI crew orchestration library** that enables declaring crews once and running them on **CrewAI**, **LangGraph**, or **AWS Strands** depending on what's installed.

## Critical: GitHub Authentication

```bash
# ALWAYS use GITHUB_JBCOM_TOKEN for jbcom repos
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command>
```

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Lint and format
uvx ruff check src/ tests/
uvx ruff format src/ tests/

# Run a crew (auto-detects best framework)
uv run agentic-crew run <package> <crew> --input "..."
```

## Architecture

### Core Concept: Framework Decomposition

```
┌─────────────────────────────────────────────────────────────────┐
│                    agentic-crew                                  │
│                                                                  │
│  manifest.yaml → Loader → Framework Decomposer → Runner          │
│                               │                                  │
│              ┌────────────────┼────────────────┐                │
│              ▼                ▼                ▼                │
│         CrewAI            LangGraph         Strands             │
│         Runner             Runner            Runner             │
└─────────────────────────────────────────────────────────────────┘
```

The key insight: **Declare once, run anywhere**. A crew defined in YAML can be:
- Run on CrewAI (default, if installed)
- Run on LangGraph (if CrewAI not available)
- Run on Strands (if neither available)

### Directory Structure

```
src/agentic_crew/
├── core/                    # Framework-agnostic core
│   ├── discovery.py         # Find .crewai/ directories
│   ├── loader.py            # Load YAML configs
│   ├── runner.py            # Execute crews
│   └── decomposer.py        # NEW: Framework decomposition
├── runners/                 # NEW: Framework-specific runners
│   ├── __init__.py
│   ├── base.py              # Abstract base runner
│   ├── crewai_runner.py     # CrewAI implementation
│   ├── langgraph_runner.py  # LangGraph implementation
│   └── strands_runner.py    # Strands implementation
├── base/
│   └── archetypes.yaml      # Reusable agent templates
├── tools/
│   └── file_tools.py        # Shared file tools
└── crews/                   # Example crews
```

### Manifest Format (.crewai/manifest.yaml)

```yaml
name: my-package
version: "1.0"
description: Package description

# LLM configuration
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514

# Crew definitions
crews:
  my_crew:
    description: What this crew does
    agents: crews/my_crew/agents.yaml
    tasks: crews/my_crew/tasks.yaml
    knowledge:
      - knowledge/domain_docs
    
    # Optional: Framework preferences
    preferred_framework: crewai  # or langgraph, strands, auto
```

## Development Commands

```bash
# Install with all dev dependencies
uv sync --extra dev --extra tests

# Run specific test file
uv run pytest tests/test_discovery.py -v

# Run with coverage
uv run pytest tests/ --cov=agentic_crew --cov-report=term-missing

# Type checking
uv run mypy src/

# Format code
uvx ruff format src/ tests/
uvx ruff check src/ tests/ --fix
```

## Code Style

- Python 3.11+ required
- Ruff for linting/formatting (100 char line length)
- Type hints on all public functions
- Google-style docstrings
- Absolute imports

## Commit Messages

Use conventional commits:
- `feat(core): add framework decomposition` → minor
- `fix(runners): fix LangGraph state handling` → patch
- `docs: update AGENTS.md` → no release
- `refactor(loader): simplify YAML parsing` → no release

## Key Patterns

### 1. Framework Detection

```python
from agentic_crew.core.decomposer import detect_framework, get_runner

# Auto-detect best available framework
framework = detect_framework()  # Returns "crewai", "langgraph", or "strands"

# Get the appropriate runner
runner = get_runner(framework)
```

### 2. Crew Definition

```python
# Load and run a crew
from agentic_crew import run_crew

result = run_crew(
    package="vendor-connectors",
    crew="connector_builder",
    inputs={"api_docs_url": "https://docs.meshy.ai/en"}
)
```

### 3. Tool Registration

```python
# Tools are registered once, work with all frameworks
from agentic_crew.tools import register_tool

@register_tool
def scrape_docs(url: str) -> str:
    """Scrape documentation from URL."""
    # Implementation
```

## Testing

### Unit Tests
```bash
uv run pytest tests/ -v --ignore=tests/e2e
```

### E2E Tests (requires API keys)
```bash
uv run pytest tests/e2e/ --e2e -v
```

## Environment Variables

- `ANTHROPIC_API_KEY` - Required for Claude LLM
- `GITHUB_JBCOM_TOKEN` - Required for GitHub operations
- `MESHY_API_KEY` - For Meshy-related crews (optional)

## Common Tasks

### Adding a New Crew

1. Create directory: `.crewai/crews/my_crew/`
2. Add `agents.yaml` with agent definitions
3. Add `tasks.yaml` with task definitions
4. Register in `.crewai/manifest.yaml`
5. Test: `uv run agentic-crew run <package> my_crew --input "test"`

### Adding Framework Support

1. Create runner in `src/agentic_crew/runners/`
2. Implement `BaseRunner` interface
3. Register in `decomposer.py`
4. Add tests in `tests/test_runners.py`

## Session Management

```bash
# Start of session
cat memory-bank/activeContext.md 2>/dev/null || echo "No memory bank"

# End of session - update context
echo "## Session: $(date +%Y-%m-%d)" >> memory-bank/activeContext.md
```

## Related Repositories

- `vendor-connectors` - HTTP connector library (uses agentic-crew for dev)
- `otterfall` - Game project (uses agentic-crew for game dev crews)
- `directed-inputs-class` - Credential management

## Key Files

| File | Purpose |
|------|---------|
| `src/agentic_crew/core/decomposer.py` | Framework auto-detection and selection |
| `src/agentic_crew/runners/base.py` | Abstract runner interface |
| `src/agentic_crew/core/loader.py` | YAML config to crew objects |
| `crewbase.yaml` | Development crew configuration |
