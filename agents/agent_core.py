import logging
from typing import Any, Dict, Optional
from tools.llm_client import LLMClient
from tools.tool_factory import ToolFactory

class AgentCore:
    """Base class for all agents in AetherFlow."""
    
    def __init__(self, llm_client: LLMClient = None, config: Optional[Dict] = None, name: str = None):
        self.name = name or self.__class__.__name__
        self.llm_client = llm_client
        self.config = config or {}
        self.tools = {}
        self.logger = logging.getLogger(self.name)
        self.logger.info(f"🛠️ {self.name} initialized.")
        self.tool_factory = ToolFactory(config, llm_client)
        
    def register_tool(self, tool_name: str, tool_obj: Any):
        """Registers a tool for the agent to use."""
        self.tools[tool_name] = tool_obj
        
    def use_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """Uses a registered tool if available."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found.")
        return tool.run(*args, **kwargs)
    
    def get_tool(self, tool_name, tool_config=None):
        """Get or create a tool by name."""
        tool = self.tool_factory.get_tool(tool_name, tool_config)
        if tool:
            self.tools[tool_name] = tool
        return tool
    
    def execute_with_tools(self, task):
        """Identifies and uses appropriate tools to complete a task."""
        self.logger.info(f"🛠️ Executing with tools: {task}")
        
        # Analyze what tools are needed for this task
        tools_analysis_prompt = f"""
        Task: {task}
        
        What tools from the following list would be needed to complete this task?
        - web_scraper: For fetching web content
        - data_extractor: For extracting structured data from text
        - html_generator: For creating HTML pages
        - filesystem: For reading/writing files
        - api: For making API calls
        
        Return only the tool names as a comma-separated list, no explanation.
        """
        
        tools_needed = self.llm_client.generate_response(tools_analysis_prompt).strip()
        tool_names = [name.strip() for name in tools_needed.split(',')]
        
        # Initialize the needed tools
        for tool_name in tool_names:
            self.get_tool(tool_name)
        
        return tool_names
    
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