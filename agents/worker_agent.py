import logging
import re
import os
from agents.agent_core import AgentCore

class WorkerAgent(AgentCore):
    """Agent responsible for executing assigned tasks."""

    def __init__(self, llm_client, config=None):
        super().__init__(llm_client, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure filesystem tool is available
        if "filesystem" not in self.tools:
            from tools.filesystem_tool import FileSystemTool
            self.register_tool("filesystem", FileSystemTool("filesystem", self.config.get("tools", {}).get("filesystem", {})))

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
    
    def extract_code(self, text, language="python"):
        """Extract code from text, handling markdown code blocks."""
        # Try to find code within markdown code blocks
        pattern = rf"```(?:{language})?([^`]+)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks found, return the original text
        return text
    
    def detect_file_operations(self, task):
        """Detect if task involves file operations and extract file paths."""
        # Pattern to match save operations
        save_patterns = [
            r"save (?:to|as|in|at) (?:the )?(?:file )?(?:path )?[\"']?([^\"'\s]+)[\"']?",
            r"(?:create|write|output) (?:a )?(?:file )?(?:at|to|in) [\"']?([^\"'\s]+)[\"']?",
            r"generate .*? (?:file|code|script) .*? (?:to|in|at) [\"']?([^\"'\s]+)[\"']?"
        ]
        
        for pattern in save_patterns:
            match = re.search(pattern, task.lower())
            if match:
                return "save", match.group(1)
        
        # Pattern to match read operations
        read_patterns = [
            r"read (?:from )?(?:the )?(?:file )?(?:at )?[\"']?([^\"'\s]+)[\"']?",
            r"load (?:from )?(?:the )?(?:file )?(?:at )?[\"']?([^\"'\s]+)[\"']?"
        ]
        
        for pattern in read_patterns:
            match = re.search(pattern, task.lower())
            if match:
                return "read", match.group(1)
        
        return None, None

    def act(self, task: str) -> str:
        """Executes the given task."""
        self.logger.info(f"⚡ Executing task: {task}")
        
        # First think about the approach
        self.think(task)
        
        # Detect if task involves file operations
        operation, file_path = self.detect_file_operations(task)
        
        # Then execute the task
        execution_prompt = (
            "You are a skilled assistant tasked with completing the following request. "
            "Provide a thoughtful, helpful, and accurate response.\n\n"
            f"Request: {task}\n\n"
            "Your response:"
        )
        
        result = self.llm_client.generate_response(execution_prompt)
        
        # Handle file operations if detected
        if operation == "save" and file_path:
            self.logger.info(f"Detected save operation to file: {file_path}")
            
            # Extract code if present
            code_content = self.extract_code(result)
            
            # Save to file
            save_result = self.tools["filesystem"].run("write", file_path, code_content)
            
            if save_result.get("success"):
                save_message = f"\n\n✅ Successfully saved code to: {save_result.get('file_path')}"
                self.logger.info(f"File saved successfully to: {save_result.get('file_path')}")
            else:
                save_message = f"\n\n❌ Failed to save code: {save_result.get('error')}"
                self.logger.error(f"Failed to save file: {save_result.get('error')}")
            
            # Append save result to the response
            result += save_message
        
        return result