import logging
import json
from typing import Dict
from agents.agent_core import AgentCore

class AgentCreatorAgent(AgentCore):
    """Agent responsible for creating and configuring new specialized agents.
    
    @agent_metadata{"description": "Specializes in creating and configuring new agents", "capabilities": ["agent creation", "code generation", "specialization", "agent design"]}
    """

    def __init__(self, llm_client, config: Dict):
        super().__init__(llm_client, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("🛠️ AgentCreatorAgent initialized.")

    def analyze_requirements(self, task):
        """Analyzes the task to determine appropriate agent capabilities."""
        self.logger.info(f"🔍 Analyzing requirements for task: {task}")
        
        analysis_prompt = f"""
        Analyze this task and determine the ideal specialized agent capabilities:
        
        {task}
        
        Respond with JSON only:
        {{
            "agent_name": "descriptive_name_with_underscores",
            "description": "Precise description of agent's purpose",
            "capabilities": ["capability1", "capability2", "capability3"],
            "required_methods": ["method1", "method2"]
        }}
        """
        
        analysis = self.llm_client.generate_response(analysis_prompt)
        return json.loads(analysis)
    
    def generate_agent_code(self, specs):
        """Generates code for a new agent based on specifications."""
        self.logger.info(f"💻 Generating agent code for: {specs['agent_name']}")
        
        code_prompt = f"""
        Create a Python agent class with these specifications:
        - Name: {specs['agent_name'].title()}Agent
        - Description: {specs['description']}
        - Capabilities: {', '.join(specs['capabilities'])}
        - Required methods: {', '.join(specs['required_methods'])}
        
        The agent must:
        1. Inherit from AgentCore
        2. Have an 'act' method that takes a task parameter
        3. Include proper logging
        4. Have a docstring with @agent_metadata containing capabilities
        5. Be well-commented and follow best practices
        
        Return only valid Python code, no explanations.
        """
        
        return self.llm_client.generate_response(code_prompt)
    
    def act(self, task):
        """Creates a new specialized agent based on the task requirements."""
        self.logger.info("🤖 Creating new specialized agent")
        
        try:
            # Analyze the task to determine agent specs
            specs = self.analyze_requirements(task)
            
            # Generate the agent code
            agent_code = self.generate_agent_code(specs)
            
            # Save the agent to a file
            from tools.agent_manager import AgentManager
            agent_manager = AgentManager(self.llm_client, save_enabled=True)
            agent_name = specs["agent_name"]
            
            # Save to dynamic_agents directory
            import os
            file_path = os.path.join(agent_manager.dynamic_agents_directory, f"{agent_name}_agent.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(agent_code)
            self.logger.info(f"✅ Successfully created agent file: {file_path}")
            
            # Register the new agent
            agent_manager.scan_and_append_agents()
            
            return f"✨ Created new agent: {agent_name}_agent.py with capabilities: {', '.join(specs['capabilities'])}"
        except Exception as e:
            self.logger.error(f"❌ Failed to create agent: {e}")
            return f"⚠️ Error creating agent: {str(e)}"