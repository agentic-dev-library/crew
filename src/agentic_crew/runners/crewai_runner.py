"""CrewAI runner implementation.

This is the default and most full-featured runner. CrewAI provides:
- Hierarchical and sequential processes
- Memory and planning
- Knowledge sources
- Tool integration
- Delegation between agents
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_crew.runners.base import BaseRunner


class CrewAIRunner(BaseRunner):
    """Runner that uses CrewAI for crew execution."""

    framework_name = "crewai"

    def __init__(self):
        """Initialize CrewAI runner."""
        # Verify CrewAI is available
        try:
            import crewai  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "CrewAI not installed. Install with: pip install crewai[tools]"
            ) from e

    def build_crew(self, crew_config: dict[str, Any]) -> Any:
        """Build a CrewAI Crew from configuration.

        Args:
            crew_config: Universal crew configuration.

        Returns:
            CrewAI Crew object.
        """
        from crewai import Crew, Process

        # Build agents
        agents_config = crew_config.get("agents", {})
        agents = {}
        for agent_name, agent_cfg in agents_config.items():
            agents[agent_name] = self.build_agent(agent_cfg)

        # Build tasks
        tasks_config = crew_config.get("tasks", {})
        tasks = []
        for task_name, task_cfg in tasks_config.items():
            agent_name = task_cfg.get("agent")
            if not agent_name or agent_name not in agents:
                raise ValueError(f"Task '{task_name}' has invalid agent: {agent_name}")
            tasks.append(self.build_task(task_cfg, agents[agent_name]))

        # Load knowledge sources
        knowledge_sources = self._load_knowledge(crew_config.get("knowledge_paths", []))

        # Determine process type
        process_type = crew_config.get("process", "sequential")
        process = Process.hierarchical if process_type == "hierarchical" else Process.sequential

        return Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=process,
            planning=crew_config.get("planning", True),
            memory=crew_config.get("memory", True),
            knowledge_sources=knowledge_sources if knowledge_sources else None,
            verbose=crew_config.get("verbose", True),
        )

    def run(self, crew: Any, inputs: dict[str, Any]) -> str:
        """Execute the CrewAI crew.

        Args:
            crew: CrewAI Crew object.
            inputs: Inputs for the crew.

        Returns:
            Crew output as string.
        """
        result = crew.kickoff(inputs=inputs)
        return result.raw if hasattr(result, "raw") else str(result)

    def build_agent(self, agent_config: dict[str, Any], tools: list | None = None) -> Any:
        """Build a CrewAI Agent.

        Args:
            agent_config: Agent configuration.
            tools: Optional tools for the agent.

        Returns:
            CrewAI Agent object.
        """
        from crewai import Agent

        return Agent(
            role=agent_config.get("role", "Agent"),
            goal=agent_config.get("goal", ""),
            backstory=agent_config.get("backstory", ""),
            llm=self.get_llm(agent_config.get("llm")),
            tools=tools or [],
            allow_delegation=agent_config.get("allow_delegation", False),
            verbose=True,
        )

    def build_task(self, task_config: dict[str, Any], agent: Any) -> Any:
        """Build a CrewAI Task.

        Args:
            task_config: Task configuration.
            agent: Agent to assign to the task.

        Returns:
            CrewAI Task object.
        """
        from crewai import Task

        return Task(
            description=task_config.get("description", ""),
            expected_output=task_config.get("expected_output", ""),
            agent=agent,
        )

    def _load_knowledge(self, knowledge_paths: list[Path]) -> list:
        """Load knowledge sources from paths.

        Args:
            knowledge_paths: List of knowledge directory paths.

        Returns:
            List of CrewAI knowledge source objects.
        """
        from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

        sources = []
        for knowledge_path in knowledge_paths:
            if not isinstance(knowledge_path, Path):
                knowledge_path = Path(knowledge_path)
            if not knowledge_path.exists():
                continue

            for ext in ["*.md", "*.txt", "*.py", "*.ts"]:
                for file_path in knowledge_path.rglob(ext):
                    try:
                        content = file_path.read_text()
                        if content.strip():
                            sources.append(TextFileKnowledgeSource(file_paths=[str(file_path)]))
                    except OSError:
                        pass

        return sources
