"""AWS Strands runner implementation.

Strands is lightweight and AWS-native, good for:
- Simple agent workflows
- AWS Bedrock integration
- Minimal dependencies
- Plain Python function tools
"""

from __future__ import annotations

from typing import Any

from agentic_crew.runners.base import BaseRunner


class StrandsRunner(BaseRunner):
    """Runner that uses AWS Strands for crew execution."""

    framework_name = "strands"

    def __init__(self):
        """Initialize Strands runner."""
        try:
            import strands  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "Strands not installed. Install with: pip install strands-agents"
            ) from e

    def build_crew(self, crew_config: dict[str, Any]) -> Any:
        """Build a Strands agent from configuration.

        Strands uses a single-agent model, so we combine crew tasks
        into a system prompt for one capable agent.

        Args:
            crew_config: Universal crew configuration.

        Returns:
            Strands Agent object.
        """
        from strands import Agent

        # Build system prompt from crew description and agent backstories
        system_prompt = self._build_system_prompt(crew_config)

        # Collect tools from tasks
        tools = self._collect_tools(crew_config)

        return Agent(
            system_prompt=system_prompt,
            tools=tools,
        )

    def run(self, crew: Any, inputs: dict[str, Any]) -> str:
        """Execute the Strands agent.

        Args:
            crew: Strands Agent object.
            inputs: Inputs for the agent.

        Returns:
            Agent output as string.
        """
        # Convert inputs to prompt
        prompt = inputs.get("input", inputs.get("task", str(inputs)))

        result = crew(prompt)

        return str(result)

    def build_agent(self, agent_config: dict[str, Any], tools: list | None = None) -> Any:
        """Build a Strands agent.

        Args:
            agent_config: Agent configuration.
            tools: Optional tools.

        Returns:
            Strands Agent object.
        """
        from strands import Agent

        system_prompt = (
            f"You are a {agent_config.get('role', 'helpful assistant')}.\n\n"
            f"Goal: {agent_config.get('goal', '')}\n\n"
            f"Background: {agent_config.get('backstory', '')}"
        )

        return Agent(
            system_prompt=system_prompt,
            tools=tools or [],
        )

    def build_task(self, task_config: dict[str, Any], agent: Any) -> Any:
        """Build a task for Strands.

        In Strands, tasks are prompts to the agent. Returns a dict
        that can be used to construct prompts.

        Args:
            task_config: Task configuration.
            agent: Agent for the task.

        Returns:
            Task configuration dict.
        """
        return {
            "description": task_config.get("description", ""),
            "expected_output": task_config.get("expected_output", ""),
            "agent": agent,
        }

    def _build_system_prompt(self, crew_config: dict[str, Any]) -> str:
        """Build a comprehensive system prompt from crew config.

        Combines all agent roles, goals, and backstories into a single
        capable system prompt.

        Args:
            crew_config: Crew configuration.

        Returns:
            System prompt string.
        """
        parts = []

        # Add crew description
        if crew_config.get("description"):
            parts.append(f"# Your Purpose\n{crew_config['description']}")

        # Add agent capabilities
        agents = crew_config.get("agents", {})
        if agents:
            parts.append("\n# Your Capabilities")
            for agent_name, agent_cfg in agents.items():
                role = agent_cfg.get("role", agent_name)
                goal = agent_cfg.get("goal", "")
                parts.append(f"\n## {role}")
                if goal:
                    parts.append(f"Goal: {goal}")

        # Add task context
        tasks = crew_config.get("tasks", {})
        if tasks:
            parts.append("\n# Tasks You Can Perform")
            for task_name, task_cfg in tasks.items():
                desc = task_cfg.get("description", "")
                if desc:
                    parts.append(f"\n- {task_name}: {desc[:200]}...")

        return "\n".join(parts)

    def _collect_tools(self, crew_config: dict[str, Any]) -> list:
        """Collect tools from crew configuration.

        Args:
            crew_config: Crew configuration.

        Returns:
            List of tool functions.
        """
        # For now, return empty - tools should be provided separately
        # Could be enhanced to auto-discover tools from task definitions
        return []
