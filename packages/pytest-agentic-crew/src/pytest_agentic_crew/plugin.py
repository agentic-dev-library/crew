"""Pytest plugin for agentic-crew E2E test fixtures.

This module is registered as a pytest plugin via entry points.
All fixtures and hooks are automatically available when the package is installed.

Includes VCR.py integration for recording/replaying LLM API calls.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import pytest

# Import VCR fixtures (they register themselves)
from pytest_agentic_crew.vcr import (
    _vcr_marker,  # noqa: F401
    vcr,  # noqa: F401
    vcr_cassette,  # noqa: F401
    vcr_cassette_dir,  # noqa: F401
    vcr_cassette_name,  # noqa: F401
    vcr_config,  # noqa: F401
)
from pytest_agentic_crew.vcr import pytest_addoption as vcr_addoption

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def pytest_addoption(parser: Any) -> None:
    """Add custom command line options for E2E tests.

    Options:
        --e2e: Enable E2E tests (disabled by default)
        --framework: Filter tests by framework (crewai, langgraph, strands)
        --vcr-record: VCR recording mode (once, new_episodes, none, all)
        --disable-vcr: Disable VCR cassette recording/playback
    """
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="Run E2E tests (require API keys and make real LLM calls)",
    )
    parser.addoption(
        "--framework",
        action="store",
        default=None,
        help="Run E2E tests for specific framework only (crewai, langgraph, or strands)",
    )
    # Add VCR options
    vcr_addoption(parser)


def pytest_collection_modifyitems(config: Any, items: list[pytest.Item]) -> None:
    """Modify test collection to handle E2E and framework filtering.

    Behavior:
        - Tests marked with @pytest.mark.e2e are skipped unless --e2e flag is set
        - When --framework=<name> is set, only tests with matching marker run
    """
    e2e_enabled = config.getoption("--e2e")
    framework_filter = config.getoption("--framework")

    skip_e2e = pytest.mark.skip(reason="E2E tests disabled (need --e2e flag)")
    skip_framework = pytest.mark.skip(
        reason=f"Test not for framework '{framework_filter}' (--framework filter)"
    )

    for item in items:
        if "e2e" in item.keywords and not e2e_enabled:
            item.add_marker(skip_e2e)

        if framework_filter:
            framework_markers = {"crewai", "langgraph", "strands"}
            test_frameworks = framework_markers.intersection(item.keywords)
            # Only skip if the test is marked with a framework and it doesn't match the filter.
            if test_frameworks and framework_filter not in test_frameworks:
                item.add_marker(skip_framework)


# =============================================================================
# API Key Check Fixtures
# =============================================================================


@pytest.fixture
def check_api_key() -> None:
    """Check that ANTHROPIC_API_KEY is available.

    Raises:
        pytest.skip: If ANTHROPIC_API_KEY is not set.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")


@pytest.fixture
def check_aws_credentials() -> None:
    """Check that AWS credentials are available for Bedrock.

    Raises:
        pytest.skip: If AWS credentials are not configured.
    """
    has_key = os.environ.get("AWS_ACCESS_KEY_ID")
    has_profile = os.environ.get("AWS_PROFILE")
    if not (has_key or has_profile):
        pytest.skip("AWS credentials not configured (need AWS_ACCESS_KEY_ID or AWS_PROFILE)")


# =============================================================================
# Framework Mocking Fixtures
# =============================================================================

# List of framework modules to mock for unit testing
FRAMEWORK_MODULES = [
    "crewai",
    "crewai.knowledge",
    "crewai.knowledge.source",
    "crewai.knowledge.source.text_file_knowledge_source",
    "langgraph",
    "langgraph.prebuilt",
    "langchain_anthropic",
    "strands",
]


@pytest.fixture
def mock_frameworks(mocker: MockerFixture) -> Generator[dict[str, Any], None, None]:
    """Fixture to mock AI framework modules for unit testing.

    This fixture mocks all framework modules (crewai, langgraph, strands) so that
    tests can run without the actual frameworks installed. Use this for unit tests
    that need to test runner behavior without making real framework calls.

    Yields:
        dict: Dictionary mapping module names to their mock objects.

    Example:
        def test_crewai_runner(mock_frameworks):
            from agentic_crew.runners.crewai_runner import CrewAIRunner
            runner = CrewAIRunner()
            # Test runner behavior with mocked framework
    """
    original_modules: dict[str, Any] = {}
    mock_modules: dict[str, Any] = {}

    # Create mocks and backup originals
    for module_name in FRAMEWORK_MODULES:
        mock_modules[module_name] = mocker.MagicMock()
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = mock_modules[module_name]

    yield mock_modules

    # Restore original modules
    for module_name in FRAMEWORK_MODULES:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            sys.modules.pop(module_name, None)


@pytest.fixture
def mock_crewai(mocker: MockerFixture) -> Generator[dict[str, Any], None, None]:
    """Fixture to mock only CrewAI framework modules.

    Use this when testing CrewAI-specific functionality without needing
    all framework mocks.

    Yields:
        dict: Dictionary with CrewAI mock objects.
    """
    crewai_modules = [
        "crewai",
        "crewai.knowledge",
        "crewai.knowledge.source",
        "crewai.knowledge.source.text_file_knowledge_source",
    ]

    original_modules: dict[str, Any] = {}
    mock_modules: dict[str, Any] = {}

    for module_name in crewai_modules:
        mock_modules[module_name] = mocker.MagicMock()
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = mock_modules[module_name]

    yield mock_modules

    for module_name in crewai_modules:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            sys.modules.pop(module_name, None)


@pytest.fixture
def mock_langgraph(mocker: MockerFixture) -> Generator[dict[str, Any], None, None]:
    """Fixture to mock only LangGraph framework modules.

    Use this when testing LangGraph-specific functionality without needing
    all framework mocks.

    Yields:
        dict: Dictionary with LangGraph mock objects.
    """
    langgraph_modules = [
        "langgraph",
        "langgraph.prebuilt",
        "langchain_anthropic",
    ]

    original_modules: dict[str, Any] = {}
    mock_modules: dict[str, Any] = {}

    for module_name in langgraph_modules:
        mock_modules[module_name] = mocker.MagicMock()
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = mock_modules[module_name]

    yield mock_modules

    for module_name in langgraph_modules:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            sys.modules.pop(module_name, None)


@pytest.fixture
def mock_strands(mocker: MockerFixture) -> Generator[dict[str, Any], None, None]:
    """Fixture to mock only Strands framework modules.

    Use this when testing Strands-specific functionality without needing
    all framework mocks.

    Yields:
        dict: Dictionary with Strands mock objects.
    """
    strands_modules = ["strands"]

    original_modules: dict[str, Any] = {}
    mock_modules: dict[str, Any] = {}

    for module_name in strands_modules:
        mock_modules[module_name] = mocker.MagicMock()
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = mock_modules[module_name]

    yield mock_modules

    for module_name in strands_modules:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            sys.modules.pop(module_name, None)


# =============================================================================
# Crew Configuration Fixtures
# =============================================================================


@pytest.fixture
def temp_crew_dir(tmp_path: Path) -> Path:
    """Create a temporary crew directory with minimal structure.

    Returns:
        Path to the .crewai directory.
    """
    crew_dir = tmp_path / "test_package" / ".crewai"
    crew_dir.mkdir(parents=True)
    (crew_dir / "crews").mkdir()
    return crew_dir


@pytest.fixture
def simple_agent_config() -> dict[str, Any]:
    """Get a simple agent configuration for testing."""
    return {
        "role": "Test Agent",
        "goal": "Answer simple questions accurately",
        "backstory": "You are a helpful assistant focused on providing clear, concise answers.",
    }


@pytest.fixture
def simple_task_config() -> dict[str, Any]:
    """Get a simple task configuration for testing."""
    return {
        "description": "Answer the question: What is 2 + 2?",
        "expected_output": "The answer to the mathematical question",
    }


@pytest.fixture
def simple_crew_config(
    simple_agent_config: dict[str, Any],
    simple_task_config: dict[str, Any],
) -> dict[str, Any]:
    """Get a simple crew configuration for testing."""
    return {
        "name": "test_crew",
        "description": "A simple test crew",
        "agents": {
            "test_agent": simple_agent_config,
        },
        "tasks": {
            "test_task": {
                **simple_task_config,
                "agent": "test_agent",
            },
        },
        "knowledge_paths": [],
    }


@pytest.fixture
def multi_agent_crew_config() -> dict[str, Any]:
    """Get a multi-agent crew configuration for testing."""
    return {
        "name": "multi_agent_crew",
        "description": "A crew with multiple collaborating agents",
        "agents": {
            "researcher": {
                "role": "Researcher",
                "goal": "Gather and analyze information",
                "backstory": "You are an expert researcher.",
            },
            "writer": {
                "role": "Writer",
                "goal": "Write clear summaries",
                "backstory": "You are a skilled technical writer.",
            },
        },
        "tasks": {
            "research_task": {
                "description": "Research the topic: Python programming",
                "expected_output": "Key facts about Python",
                "agent": "researcher",
            },
            "writing_task": {
                "description": "Write a brief summary based on the research",
                "expected_output": "A concise summary",
                "agent": "writer",
                "context": ["research_task"],
            },
        },
        "knowledge_paths": [],
    }


@pytest.fixture
def crew_with_knowledge(tmp_path: Path) -> dict[str, Any]:
    """Get a crew configuration with knowledge sources."""
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    test_doc = knowledge_dir / "test_info.md"
    test_doc.write_text(
        """# Test Knowledge

This is test knowledge about the color blue.
Blue is a primary color.
It is often associated with calmness and stability.
"""
    )

    return {
        "name": "knowledge_crew",
        "description": "A crew with knowledge sources",
        "agents": {
            "knowledgeable_agent": {
                "role": "Knowledge Expert",
                "goal": "Answer questions using provided knowledge",
                "backstory": "You have access to specialized knowledge.",
            },
        },
        "tasks": {
            "knowledge_task": {
                "description": "What color is mentioned in the knowledge base?",
                "expected_output": "The color mentioned",
                "agent": "knowledgeable_agent",
            },
        },
        "knowledge_paths": [knowledge_dir],
    }
