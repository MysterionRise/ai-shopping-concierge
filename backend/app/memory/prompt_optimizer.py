"""Prompt optimization based on interaction outcomes.

Uses stored memories and conversation outcomes to evolve agent system prompts.
This is a background process — not in the critical path.
"""

import structlog

logger = structlog.get_logger()


class PromptOptimizer:
    def __init__(self) -> None:
        self.base_prompts: dict[str, str] = {}
        self.optimization_history: list[dict[str, object]] = []

    def register_base_prompt(self, agent_name: str, prompt: str) -> None:
        self.base_prompts[agent_name] = prompt

    def get_optimized_prompt(self, agent_name: str) -> str:
        return self.base_prompts.get(agent_name, "")

    async def record_outcome(
        self,
        agent_name: str,
        prompt_used: str,
        outcome: str,
        success: bool,
    ) -> None:
        self.optimization_history.append(
            {
                "agent": agent_name,
                "outcome": outcome,
                "success": success,
            }
        )
        logger.info(
            "Recorded prompt outcome",
            agent=agent_name,
            success=success,
        )
