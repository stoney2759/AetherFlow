import logging
from typing import Any, Dict, Optional
from tools.llm_client import LLMClient

class AgentCore:
    """Base class for all agents in AetherFlow."""
    
    def __init__(self, llm_client: LLMClient = None, config: Optional[Dict] = None, name: str = None):
        self.name = name or self.__class__.__name__
        self.llm_client = llm_client
        self.config = config or {}
        self.tools = {}
        self.logger = logging.getLogger(self.name)
        self.logger.info(f"🛠️ {self.name} initialized.")
        
    def register_tool(self, tool_name: str, tool_obj: Any):
        """Registers a tool for the agent to use."""
        self.tools[tool_name] = tool_obj
        
    def use_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """Uses a registered tool if available."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found.")
        return tool.run(*args, **kwargs)
    
    def think(self, task: str) -> str:
        """Processes a task and determines execution strategy."""
        raise NotImplementedError("Subclasses should implement this method.")
        
    def act(self, task: str) -> str:
        """Executes the given task and returns a result."""
        raise NotImplementedError("Subclasses should implement this method.")
        
    def generate_final_response(self, prompt: str) -> tuple[str, float]:
        """Processes a prompt and generates a response using the LLM."""
        if not prompt.strip():
            return "Error: Empty prompt received.", 0.0
        
        if not self.llm_client:
            self.logger.error(f"❌ {self.name} - LLMClient not initialized.")
            return "⚠️ AI Error: No LLMClient found.", 0.0
            
        try:
            response = self.llm_client.generate_response(prompt)
            self.logger.info(f"✅ {self.name} successfully processed request.")
            return response.strip(), 0.0  # Replace 0.0 with actual time if tracked
        except Exception as e:
            self.logger.error(f"⚠️ {self.name} failed to process request: {e}")
            return f"⚠️ AI Error: {str(e)}", 0.0