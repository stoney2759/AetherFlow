import os
import json
import logging
import importlib
import inspect
import re
from tools.config_loader import CONFIG
from tools.llm_client import LLMClient

# Load Debug Mode
DEBUG_MODE = CONFIG.get("debug", {}).get("debug_mode", False)

if DEBUG_MODE:
    logging.debug("🛠️ AgentManager initialized with debug mode ON.")

class AgentManager:
    """Handles agent metadata, including scanning, tracking, and updating agents."""

    def __init__(self, llm_client: LLMClient, index_file="config/agents_index.json", save_enabled=True):
        self.llm_client = llm_client
        self.index_file = index_file
        self.agents_directory = "agents"
        self.dynamic_agents_directory = "dynamic_agents"
        self.save_enabled = save_enabled
        
        # ✅ Ensure directories exist
        self.ensure_directories_exist()
        self.ensure_index_exists()
        self.agents = self.load_agents()  # ✅ Ensure agents are only loaded once

    def ensure_directories_exist(self):
        """Ensures required agent directories exist."""
        for directory in [self.agents_directory, self.dynamic_agents_directory]:
            if not os.path.exists(directory):
                os.makedirs(directory)  # ✅ Create the folder if it doesn't exist
                logging.info(f"📁 Created missing directory: {directory}")

    def ensure_index_exists(self):
        """Ensures the agents_index.json file exists and is properly formatted."""
        if not os.path.exists(self.index_file):
            logging.warning("⚠️ agents_index.json not found. Creating a new one.")
            self.save_agents({})  # ✅ Create a new empty JSON file
        else:
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        raise ValueError("Invalid format: Root should be a dictionary.")
            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"⚠️ Corrupt or missing agents_index.json. Resetting file. Error: {e}")
                self.save_agents({})  # ✅ Reset to empty JSON

    def load_agents(self):
        """Loads agent metadata from the JSON file."""
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid format: Root should be a dictionary.")
                return data
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"⚠️ Error loading agents_index.json: {e}")
            return {}

    def save_agents(self, agents):
        """Saves agent metadata to the JSON file."""
        if not self.save_enabled:
            logging.debug("Agent saving disabled - skipping save operation")
            return
            
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(agents, f, indent=4, ensure_ascii=False)
            logging.info("✅ Agents index updated successfully.")
        except Exception as e:
            logging.error(f"⚠️ Failed to save agents_index.json: {e}")

    def extract_agent_metadata(self, agent_class):
        """Extract metadata from agent class docstring."""
        docstring = inspect.getdoc(agent_class) or ""
        
        # Extract JSON metadata section
        metadata_match = re.search(r'@agent_metadata\s*(\{.*?\})', docstring, re.DOTALL)
        if metadata_match:
            try:
                metadata = json.loads(metadata_match.group(1))
                return metadata
            except json.JSONDecodeError:
                logging.warning(f"Invalid metadata JSON in {agent_class.__name__}")
        
        # Default metadata if none found
        return {
            "description": f"Auto-detected {agent_class.__name__}",
            "capabilities": []
        }
        
    def update_agent_metadata(self, agent_name, metadata):
        """Updates agent metadata from docstring if available."""
        agents = self.load_agents()
        if agent_name in agents:
            # Update only if new info is available
            if "description" in metadata and metadata["description"] != f"Auto-detected {agent_name}":
                agents[agent_name]["description"] = metadata["description"]
            if "capabilities" in metadata and metadata["capabilities"]:
                agents[agent_name]["capabilities"] = metadata["capabilities"]
            self.save_agents(agents)

    def scan_and_append_agents(self):
        """Scans for new agents in both folders and appends them to the JSON file."""
        agents = self.load_agents()
        detected_agents = {}

        # ✅ Scan both 'agents/' and 'dynamic_agents/' directories
        for agent_dir in [self.agents_directory, self.dynamic_agents_directory]:
            if not os.path.exists(agent_dir):
                continue  # Skip if directory doesn't exist (but should never happen now)

            for filename in os.listdir(agent_dir):
                if filename.endswith("_agent.py"):
                    agent_name = filename[:-3]  # Remove .py extension
                    if agent_name not in agents:
                        detected_agents[agent_name] = {
                            "description": f"Auto-detected {agent_name}",
                            "capabilities": [],
                            "usage_count": 0,
                            "success_rate": 50.0  # Default success rate
                        }
                        logging.info(f"📌 New agent detected: {agent_name}")

        if detected_agents:
            agents.update(detected_agents)
            self.save_agents(agents)
            print(f"🔍 Scanned Agents: {detected_agents}")
            logging.info("✅ New agents appended to agents_index.json.")

    def update_agent_stats(self, agent_name, success=True):
        """Updates agent usage statistics in agents_index.json."""
        agents = self.load_agents()
        if agent_name in agents:
            # Initialize usage_count if it doesn't exist
            if "usage_count" not in agents[agent_name]:
                agents[agent_name]["usage_count"] = 0
                
            agents[agent_name]["usage_count"] += 1
            
            # Initialize success_rate if it doesn't exist
            if "success_rate" not in agents[agent_name]:
                agents[agent_name]["success_rate"] = 50.0
                
            if success:
                agents[agent_name]["success_rate"] = min(100, agents[agent_name]["success_rate"] + 5)
            else:
                agents[agent_name]["success_rate"] = max(0, agents[agent_name]["success_rate"] - 5)
                
            self.save_agents(agents)
            logging.info(f"📊 Updated stats for {agent_name}: {agents[agent_name]}")
            
    def get_agent_instance(self, agent_name):
        """Instantiates and returns an agent by name."""
        if agent_name not in self.agents:
            logging.error(f"⚠️ Agent '{agent_name}' not found in agents index.")
            return None
            
        try:
            # Determine module path based on whether agent is standard or dynamic
            if os.path.exists(f"{self.agents_directory}/{agent_name}.py"):
                module_path = f"agents.{agent_name}"
            elif os.path.exists(f"{self.dynamic_agents_directory}/{agent_name}.py"):
                module_path = f"dynamic_agents.{agent_name}"
            else:
                logging.error(f"⚠️ Agent file for '{agent_name}' not found.")
                return None
                
            # Import the module
            module = importlib.import_module(module_path)
            
            # Find the agent class (assumes the class name follows CamelCase convention)
            class_name = "".join(word.capitalize() for word in agent_name.split("_"))
            if not class_name.endswith("Agent"):
                class_name += "Agent"
                
            agent_class = getattr(module, class_name, None)
            if not agent_class:
                # Fallback: look for any class that ends with 'Agent'
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name.endswith('Agent'):
                        agent_class = obj
                        break
                        
            if not agent_class:
                logging.error(f"⚠️ No agent class found in module {module_path}")
                return None
                
            # Extract metadata and update the agent's entry if needed
            metadata = self.extract_agent_metadata(agent_class)
            self.update_agent_metadata(agent_name, metadata)
                
            # Instantiate the agent with the LLM client and CONFIG 
            return agent_class(self.llm_client, CONFIG)  # Pass CONFIG instead of empty dict
                
        except Exception as e:
            logging.error(f"⚠️ Failed to instantiate agent '{agent_name}': {e}")
            return None
    
    def create_agent_with_ai(self, agent_name, description, task_types):
        """Creates a new agent using AI capabilities"""
        logging.info(f"🤖 Creating new AI-generated agent: {agent_name}")
        
        try:
            # Generate agent class code
            agent_template = self.llm_client.generate_response(
                f"Create a Python agent class named {agent_name.title()}Agent that inherits from AgentCore. "
                f"The agent should handle: {task_types}. "
                f"Include a proper docstring with @agent_metadata for capabilities."
            )
            
            # Save to file
            file_path = os.path.join(self.dynamic_agents_directory, f"{agent_name}_agent.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(agent_template)
            logging.info(f"✅ Successfully created agent file: {file_path}")
            
            # Manually add to agents index
            agents = self.load_agents()
            agents[agent_name] = {
                "description": description,
                "capabilities": task_types.split(", "),
                "usage_count": 0,
                "success_rate": 50.0
            }
            self.save_agents(agents)
            
            # Optional: Reload agents to ensure consistency
            self.agents = self.load_agents()
            
            return f"✨ Created new agent: {agent_name}_agent.py"
        except Exception as e:
            logging.error(f"❌ Failed to create agent {agent_name}: {e}")
            return f"⚠️ Error creating agent: {str(e)}"