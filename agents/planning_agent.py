import logging
from typing import Dict, Any
from agents.agent_core import AgentCore
from tools.llm_client import LLMClient

class PlanningAgent(AgentCore):
    """Agent responsible for planning and breaking down high-level goals into executable tasks.
    
    @agent_metadata{"description": "Expert at planning and breaking tasks into steps", "capabilities": ["planning", "task decomposition", "workflow", "organization"]}
    """

    def __init__(self, llm_client: LLMClient, config: Dict):
        super().__init__(llm_client, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("🛠️ PlanningAgent initialized.")

    def generate_plan(self, goal: str) -> str:
        """Generates a structured plan for achieving the given goal."""
        self.logger.info(f"PlanningAgent processing goal: {goal}")

        planning_prompt = (
            "You are an expert task planner. Given the following high-level goal, break it down into"
            " smaller, logical steps that an AI agent can execute effectively."
            "\n\nGoal: " + goal + "\n\nSteps:"
        )

        try:
            structured_plan = self.llm_client.generate_response(planning_prompt)
            return structured_plan.strip()
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return f"Error: {str(e)}"

    def act(self, goal: str):
        """Generates a plan and ensures output is a list of tasks."""
        plan = self.generate_plan(goal)
        return plan