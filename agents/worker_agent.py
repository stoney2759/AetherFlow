import logging
from agents.agent_core import AgentCore

class WorkerAgent(AgentCore):
    """Agent responsible for executing assigned tasks."""

    def __init__(self, llm_client, config=None):
        super().__init__(llm_client, config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def think(self, task: str) -> str:
        """Processes a task and determines the best execution strategy."""
        self.logger.info(f"🤔 Thinking about task: {task}")
        
        thinking_prompt = (
            "You are an expert task executor. Analyze the following task and determine "
            "the most effective approach to complete it successfully.\n\n"
            f"Task: {task}\n\n"
            "Your analysis:"
        )
        
        analysis = self.llm_client.generate_response(thinking_prompt)
        return analysis

    def act(self, task: str) -> str:
        """Executes the given task."""
        self.logger.info(f"⚡ Executing task: {task}")
        
        # First think about the approach
        self.think(task)
        
        # Then execute the task
        execution_prompt = (
            "You are a skilled assistant tasked with completing the following request. "
            "Provide a thoughtful, helpful, and accurate response.\n\n"
            f"Request: {task}\n\n"
            "Your response:"
        )
        
        result = self.llm_client.generate_response(execution_prompt)
        return result