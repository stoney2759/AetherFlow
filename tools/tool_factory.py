# tools/tool_factory.py
import logging
import importlib
import inspect
from typing import Dict, Any
from .base_tool import BaseTool

class ToolFactory:
    """Factory for creating and managing tools."""
    
    def __init__(self, config: Dict = None, llm_client=None):
        self.config = config or {}
        self.llm_client = llm_client
        self.tools = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def get_tool(self, tool_name: str, tool_config: Dict = None) -> BaseTool:
        """
        Get or create a tool by name.
        
        Args:
            tool_name: Name of the tool
            tool_config: Configuration for the tool
            
        Returns:
            BaseTool: Instantiated tool
        """
        # Check if we already have this tool
        if tool_name in self.tools:
            self.logger.debug(f"Returning existing tool: {tool_name}")
            return self.tools[tool_name]
            
        # Try to import and instantiate the tool
        try:
            # Convert tool_name to class name (e.g., web_scraper -> WebScraperTool)
            class_name = ''.join(word.capitalize() for word in tool_name.split('_')) + 'Tool'
            module_name = f"tools.{tool_name}_tool"
            
            self.logger.debug(f"Attempting to load tool: {module_name}.{class_name}")
            
            # Import the module
            module = importlib.import_module(module_name)
            
            # Get the tool class
            tool_class = getattr(module, class_name)
            
            # Create tool instance
            merged_config = {**self.config.get(tool_name, {}), **(tool_config or {})}
            tool = tool_class(name=tool_name, config=merged_config, llm_client=self.llm_client)
            
            # Store the tool
            self.tools[tool_name] = tool
            self.logger.info(f"✅ Created tool: {tool_name}")
            
            return tool
            
        except (ImportError, AttributeError) as e:
            self.logger.error(f"❌ Failed to load tool {tool_name}: {e}")
            return None
    
    def create_tool_from_spec(self, tool_spec: Dict) -> BaseTool:
        """
        Create a new tool from a specification.
        
        Args:
            tool_spec: Tool specification including name, imports, methods, etc.
            
        Returns:
            BaseTool: Dynamically created tool
        """
        # Implementation of dynamic code generation and tool creation
        # This would use the LLM to generate tool code and save it
        pass