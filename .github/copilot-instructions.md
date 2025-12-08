# GitHub Copilot Instructions for agentic-crew

## Overview

agentic-crew is a **framework-agnostic AI crew orchestration library**.

Key innovation: **Declare once, run anywhere** - crews defined in YAML can run on CrewAI, LangGraph, or Strands.

## Critical: GitHub Authentication

```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command>
```

## Development Commands

```bash
# Install
uv sync --extra dev --extra tests --extra crewai

# Test
uv run pytest tests/ -v --ignore=tests/e2e

# Lint
uvx ruff check src/ tests/ --fix
uvx ruff format src/ tests/
```

## Architecture

```
manifest.yaml → Loader → Decomposer → Runner (CrewAI/LangGraph/Strands)
```

## Key Files

| File | Purpose |
|------|---------|
| `core/decomposer.py` | Framework detection and selection |
| `runners/base.py` | Abstract runner interface |
| `runners/crewai_runner.py` | CrewAI implementation |
| `runners/langgraph_runner.py` | LangGraph implementation |
| `runners/strands_runner.py` | Strands implementation |

## Commit Messages

Use conventional commits:
- `feat(runners): add X` → minor version
- `fix(decomposer): fix Y` → patch version
- `docs: update Z` → no release

## Code Style

- Python 3.11+
- Ruff for linting (100 char line)
- Type hints required
- Google-style docstrings
