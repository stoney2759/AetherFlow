# agents/game_dev_agent.py
import json
import logging
import os
from agents.agent_core import AgentCore

class GameDevAgent(AgentCore):
    """Agent specialized in game development with Python.
    
    @agent_metadata{"description": "Specializes in creating Python games and applications", "capabilities": ["python coding", "game development", "asset creation", "testing", "debugging"]}
    """
    
    def __init__(self, llm_client, config=None):
        super().__init__(llm_client, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("🛠️ GameDevAgent initialized.")
        
        # Initialize tools
        self.get_tool("filesystem")
    
    def think(self, task):
        """Analyzes the task and determines the execution strategy."""
        self.logger.info(f"🤔 Analyzing task: {task}")
        
        thinking_prompt = f"""
        Analyze this game development task:
        
        {task}
        
        What is the best strategy to complete it? Consider:
        1. What game components need to be created?
        2. What Python libraries should be used?
        3. How should the code be structured?
        4. What assets would be needed?
        
        Provide a step-by-step plan.
        """
        
        plan = self.llm_client.generate_response(thinking_prompt)
        return plan
    
    def act(self, task):
        """Creates game code, assets, or tests based on the task."""
        self.logger.info(f"🎮 Game development task: {task}")
        
        # First, think about how to approach the task
        plan = self.think(task)
        
        # Determine task type
        task_type_prompt = f"""
        Categorize this game development task into ONE of these categories:
        - code_creation: Writing the main game code
        - asset_creation: Creating game assets (graphics, sounds, etc.)
        - testing: Testing the game functionality
        - debugging: Fixing game issues
        - documentation: Creating documentation
        
        Task: {task}
        
        Return only the category name without explanation.
        """
        
        task_type = self.llm_client.generate_response(task_type_prompt).strip().lower()
        
        # Process based on task type
        if task_type == "code_creation":
            return self._create_game_code(task)
        elif task_type == "asset_creation":
            return self._create_game_assets(task)
        elif task_type == "testing":
            return self._test_game(task)
        elif task_type == "debugging":
            return self._debug_game(task)
        elif task_type == "documentation":
            return self._create_documentation(task)
        else:
            # General implementation
            return self._general_implementation(task)
            
    def _create_game_code(self, task):
        """Creates Python game code based on task requirements."""
        code_prompt = f"""
        Create Python game code based on these requirements:
        
        {task}
        
        The code should:
        1. Use appropriate libraries (pygame, turtle, etc.)
        2. Be well-structured and commented
        3. Follow best practices for game development
        4. Be functional and runnable
        
        Return the complete, runnable Python code with appropriate imports.
        """
        
        code = self.llm_client.generate_response(code_prompt)
        
        # Save the code to a file
        fs_tool = self.tools.get("filesystem")
        if not fs_tool:
            return "Error: FileSystemTool not available"
            
        # Extract game name from task
        game_name_prompt = f"Extract a simple snake_case name for this game from the task description: {task}"
        game_name = self.llm_client.generate_response(game_name_prompt).strip().lower().replace(" ", "_")
        
        if not game_name:
            game_name = "python_game"
            
        filename = f"output/{game_name}.py"
        save_result = fs_tool.run("write", filename, code)
        
        if save_result.get("success"):
            return {
                "output": {
                    "summary": f"Created Python game code: {game_name}",
                    "result": f"Game code saved to: {save_result.get('file_path')}"
                },
                "artifacts": [
                    {
                        "name": f"{game_name} Code",
                        "description": "Main Python game code",
                        "filename": save_result.get('file_path'),
                        "content": code
                    }
                ]
            }
        else:
            return f"Error saving the game code: {save_result.get('error')}"
    
    def _create_game_assets(self, task):
        """Creates or describes game assets based on task."""
        # For text-based assets like configurations
        asset_prompt = f"""
        Create game asset descriptions or configurations based on:
        
        {task}
        
        If this is a visual asset, describe it in detail.
        If this is a configuration, provide valid JSON or Python code.
        """
        
        asset_content = self.llm_client.generate_response(asset_prompt)
        
        # Save the asset description
        fs_tool = self.tools.get("filesystem")
        if not fs_tool:
            return "Error: FileSystemTool not available"
            
        # Determine asset type and name
        asset_type_prompt = f"""
        What type of asset needs to be created based on this task?
        Options: config, image_description, sound_description, level_design
        
        Task: {task}
        
        Return only the asset type without explanation.
        """
        
        asset_type = self.llm_client.generate_response(asset_type_prompt).strip().lower()
        
        # Generate asset name
        asset_name_prompt = f"Create a short snake_case name for this asset based on: {task}"
        asset_name = self.llm_client.generate_response(asset_name_prompt).strip().lower().replace(" ", "_")
        
        if not asset_name:
            asset_name = f"game_asset_{asset_type}"
            
        # Determine file extension
        extension = ".txt"
        if asset_type == "config":
            extension = ".json"
            try:
                # Ensure it's valid JSON
                json.loads(asset_content)
            except:
                # If not valid JSON, save as text
                extension = ".txt"
                
        filename = f"output/{asset_name}{extension}"
        save_result = fs_tool.run("write", filename, asset_content)
        
        if save_result.get("success"):
            return {
                "output": {
                    "summary": f"Created game asset: {asset_name}",
                    "result": f"Asset saved to: {save_result.get('file_path')}"
                },
                "artifacts": [
                    {
                        "name": asset_name,
                        "description": f"Game asset ({asset_type})",
                        "filename": save_result.get('file_path'),
                        "content": asset_content
                    }
                ]
            }
        else:
            return f"Error saving the game asset: {save_result.get('error')}"
    
    def _test_game(self, task):
        """Creates test scenarios or code for the game."""
        test_prompt = f"""
        Create test code or test scenarios based on:
        
        {task}
        
        Include:
        1. Test scenarios to verify game functionality
        2. Test code that can be run to validate the game
        3. Expected outcomes for each test
        """
        
        test_content = self.llm_client.generate_response(test_prompt)
        
        # Save the test code
        fs_tool = self.tools.get("filesystem")
        if not fs_tool:
            return "Error: FileSystemTool not available"
            
        # Generate test name
        test_name_prompt = f"Create a short snake_case name for this test based on: {task}"
        test_name = self.llm_client.generate_response(test_name_prompt).strip().lower().replace(" ", "_")
        
        if not test_name:
            test_name = "game_test"
            
        filename = f"output/test_{test_name}.py"
        save_result = fs_tool.run("write", filename, test_content)
        
        if save_result.get("success"):
            return {
                "output": {
                    "summary": f"Created game test: {test_name}",
                    "result": f"Test saved to: {save_result.get('file_path')}"
                },
                "artifacts": [
                    {
                        "name": f"Test: {test_name}",
                        "description": "Game test code",
                        "filename": save_result.get('file_path'),
                        "content": test_content
                    }
                ]
            }
        else:
            return f"Error saving the test code: {save_result.get('error')}"
    
    def _debug_game(self, task):
        """Analyzes and fixes issues in game code."""
        # For this to work properly, the task should include the problematic code
        debug_prompt = f"""
        Debug the game code or issue described in:
        
        {task}
        
        Provide:
        1. Analysis of the issue
        2. Fixed code
        3. Explanation of the fix
        """
        
        debug_result = self.llm_client.generate_response(debug_prompt)
        
        # Extract fixed code if available
        fixed_code_prompt = f"""
        Extract ONLY the complete fixed code from this debug result:
        
        {debug_result}
        
        Return ONLY the complete fixed code, nothing else.
        """
        
        fixed_code = self.llm_client.generate_response(fixed_code_prompt)
        
        # Save the fixed code if it looks like code
        if "def " in fixed_code or "import " in fixed_code or "class " in fixed_code:
            fs_tool = self.tools.get("filesystem")
            if not fs_tool:
                return "Error: FileSystemTool not available"
                
            # Generate fixed code name
            fix_name_prompt = f"Create a short snake_case name for this fix based on: {task}"
            fix_name = self.llm_client.generate_response(fix_name_prompt).strip().lower().replace(" ", "_")
            
            if not fix_name:
                fix_name = "fixed_game_code"
                
            filename = f"output/{fix_name}.py"
            save_result = fs_tool.run("write", filename, fixed_code)
            
            if save_result.get("success"):
                return {
                    "output": {
                        "summary": "Debugging completed",
                        "analysis": debug_result,
                        "result": f"Fixed code saved to: {save_result.get('file_path')}"
                    },
                    "artifacts": [
                        {
                            "name": f"Fixed: {fix_name}",
                            "description": "Debugged and fixed game code",
                            "filename": save_result.get('file_path'),
                            "content": fixed_code
                        }
                    ]
                }
        
        # If no code to save or save failed, just return the analysis
        return {
            "output": {
                "summary": "Debugging analysis completed",
                "result": debug_result
            }
        }
    
    def _create_documentation(self, task):
        """Creates documentation for the game."""
        doc_prompt = f"""
        Create comprehensive documentation based on:
        
        {task}
        
        Include:
        1. Overview of the game
        2. How to run the game
        3. Game controls and mechanics
        4. Code structure explanation
        5. Future improvements
        
        Format as Markdown.
        """
        
        doc_content = self.llm_client.generate_response(doc_prompt)
        
        # Save the documentation
        fs_tool = self.tools.get("filesystem")
        if not fs_tool:
            return "Error: FileSystemTool not available"
            
        # Generate documentation name
        doc_name_prompt = f"Create a short snake_case name for this documentation based on: {task}"
        doc_name = self.llm_client.generate_response(doc_name_prompt).strip().lower().replace(" ", "_")
        
        if not doc_name:
            doc_name = "game_documentation"
            
        filename = f"output/{doc_name}.md"
        save_result = fs_tool.run("write", filename, doc_content)
        
        if save_result.get("success"):
            return {
                "output": {
                    "summary": f"Created game documentation: {doc_name}",
                    "result": f"Documentation saved to: {save_result.get('file_path')}"
                },
                "artifacts": [
                    {
                        "name": f"Documentation: {doc_name}",
                        "description": "Game documentation",
                        "filename": save_result.get('file_path'),
                        "content": doc_content
                    }
                ]
            }
        else:
            return f"Error saving the documentation: {save_result.get('error')}"
    
    def _general_implementation(self, task):
        """General implementation for tasks that don't fit specific categories."""
        general_prompt = f"""
        Implement the following game development task:
        
        {task}
        
        Provide:
        1. Complete implementation
        2. Any code, assets, or configurations needed
        3. Instructions for using the implementation
        """
        
        implementation = self.llm_client.generate_response(general_prompt)
        
        # Save the implementation
        fs_tool = self.tools.get("filesystem")
        if not fs_tool:
            return "Error: FileSystemTool not available"
            
        # Generate implementation name
        impl_name_prompt = f"Create a short snake_case name for this implementation based on: {task}"
        impl_name = self.llm_client.generate_response(impl_name_prompt).strip().lower().replace(" ", "_")
        
        if not impl_name:
            impl_name = "game_implementation"
            
        # Determine file extension
        extension = ".py" if "import " in implementation or "def " in implementation else ".txt"
        
        filename = f"output/{impl_name}{extension}"
        save_result = fs_tool.run("write", filename, implementation)
        
        if save_result.get("success"):
            return {
                "output": {
                    "summary": f"Created implementation: {impl_name}",
                    "result": f"Implementation saved to: {save_result.get('file_path')}"
                },
                "artifacts": [
                    {
                        "name": impl_name,
                        "description": "Game implementation",
                        "filename": save_result.get('file_path'),
                        "content": implementation
                    }
                ]
            }
        else:
            return f"Error saving the implementation: {save_result.get('error')}"