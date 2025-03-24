import logging
from typing import Any, Dict
from tools.llm_client import LLMClient  # ✅ Include LLM handling

class AgentTemplate:
    """Template class for all AI agents. Provides common functionality for agent execution."""

    def __init__(self, name: str, llm_client: LLMClient, config: Dict):
        self.name = name
        self.llm_client = llm_client  # ✅ Store LLM client for agent processing
        self.config = config
        self.tools: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def register_tool(self, tool_name: str, tool_obj: Any):
        """Registers a tool for the agent to use."""
        self.tools[tool_name] = tool_obj

    def use_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """Uses a registered tool if available."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found.")
        return tool.run(*args, **kwargs)

    def generate_final_response(self, prompt: str) -> tuple[str, float]:
        """Processes a prompt and generates a response using the LLM."""
        if not prompt.strip():
            return "Error: Empty prompt received.", 0.0
        
        try:
            response = self.llm_client.generate_response(prompt)
            return response.strip(), 0.0  # Replace 0.0 with actual elapsed time if needed
        except Exception as e:
            self.logger.error(f"⚠️ Agent response failed: {e}")
            return f"Error: {str(e)}", 0.0

    def think(self, task: str) -> str:
        """Placeholder method for agent thinking logic."""
        raise NotImplementedError("Subclasses should implement this method.")

    def act(self, task: str) -> Any:
        """Placeholder method for agent action execution."""
        raise NotImplementedError("Subclasses should implement this method.")
