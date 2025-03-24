import time
import json
import traceback
import re
from utils.logging_utils import get_logger
from tools.agent_manager import AgentManager
from tools.config_loader import CONFIG
from agents.prompt_generator_agent import PromptGeneratorAgent

# Setup logger
logger = get_logger(__name__)

class TaskRouter:
    """Routes tasks to the most suitable agent using a hybrid approach (predefined + dynamic agents)."""

    def __init__(self, llm_client):
        logger.info("🚀 Initializing TaskRouter")
        self.start_time = time.time()
        self.llm_client = llm_client
        self.agent_manager = AgentManager(llm_client, save_enabled=True)
        self.agents = self.load_agents()
        self.prompt_generator = PromptGeneratorAgent(llm_client)
        logger.debug(f"🕒 TaskRouter initialization time: {time.time() - self.start_time:.4f} seconds")

    def load_agents(self):
        """Loads agents from the AgentManager."""
        method_start = time.time()
        logger.info("🔄 Loading agents from AgentManager")
        
        agents = self.agent_manager.load_agents()
        if not agents:
            logger.warning("⚠️ No agents found in agents_index.json. Scanning for new agents...")
            self.agent_manager.scan_and_append_agents()
            agents = self.agent_manager.load_agents()
        
        load_time = time.time() - method_start
        logger.debug(f"🕒 Agent loading time: {load_time:.4f} seconds")
        logger.info(f"✅ Loaded {len(agents)} agents")
        return agents

    def refine_task(self, task):
        """Uses AI to refine the user input before routing it to an agent."""
        method_start = time.time()
        logger.info(f"Refining task input: {task}")
        
        try:
            # Only refine the prompt, don't generate a full response
            refined_task = self.prompt_generator.refine_prompt(task)
            refined_task = refined_task.strip() if refined_task else task
            
            # Update the stats for prompt_generator_agent
            self.agent_manager.update_agent_stats("prompt_generator_agent", success=True)
            
            refine_time = time.time() - method_start
            logger.debug(f"Task refinement time: {refine_time:.4f} seconds")
            logger.info(f"Refined task: {refined_task}")
            
            return refined_task
        except Exception as e:
            # Update stats on failure
            self.agent_manager.update_agent_stats("prompt_generator_agent", success=False)
            
            logger.error(f"Task refinement failed: {e}")
            return task

    def select_agent(self, task):
        """Selects the most suitable agent based on semantic matching of capabilities to task."""
        method_start = time.time()
        logger.info(f"🎯 Selecting best agent for task: {task}")
        
        if not self.agents:
            logger.warning("⚠️ No agents available for selection")
            return None
        
        # Create AI agent selection prompt
        system_message = """
        You are an agent router that must select the most suitable agent for a user task.
        Analyze the task description and the available agents with their capabilities.
        Return only the name of the best matching agent, with no other text.
        """
        
        agent_descriptions = []
        for agent_name, agent_data in self.agents.items():
            capabilities = agent_data.get("capabilities", [])
            description = agent_data.get("description", "")
            agent_descriptions.append(f"- {agent_name}: {description} (Capabilities: {', '.join(capabilities)})")
        
        prompt = f"""
        Task to route: {task}
        
        Available agents:
        {chr(10).join(agent_descriptions)}
        
        Determine which agent is best suited to handle this task based on their capabilities and description.
        Return ONLY the agent name, nothing else. If no agent is suitable, return "none".
        """
        
        try:
            # Use LLM to select the best agent
            best_agent = self.llm_client.generate_response(prompt).strip().lower()
            
            # Check if we got a valid agent
            if best_agent in self.agents:
                logger.info(f"✅ Selected agent: {best_agent}")
                success_rate = self.agents[best_agent].get("success_rate", 50.0)
                logger.debug(f"⏱️ Agent selection time: {time.time() - method_start:.4f} seconds")
                return best_agent
            elif "none" in best_agent or "no agent" in best_agent:
                logger.warning(f"⚠️ No suitable agent found for task")
                return None
            else:
                # Try partial match
                for agent_name in self.agents:
                    if agent_name in best_agent:
                        logger.info(f"✅ Selected agent via partial match: {agent_name}")
                        return agent_name
                
                logger.warning(f"⚠️ AI suggested invalid agent: {best_agent}")
                return None
        except Exception as e:
            logger.error(f"❌ Agent selection failed: {e}")
            return None

    def create_specialized_agent(self, task):
        """Creates a specialized agent for the given task."""
        logger.info("🧪 Creating specialized agent for task")
        
        # Generate a suitable agent name and description
        agent_creation_prompt = f"""
        Based on the following task, suggest a specialized agent name, description, and capabilities in strict JSON format:
        Task: {task}
        
        JSON Format (MUST be valid JSON):
        {{
            "agent_name": "descriptive_lowercase_name_with_underscores",
            "description": "Concise description of the agent's purpose",
            "capabilities": ["capability1", "capability2"]
        }}
        
        IMPORTANT: Ensure the JSON is valid and properly formatted.
        """
        
        try:
            response = self.llm_client.generate_response(agent_creation_prompt)
            logger.debug(f"Raw LLM Response: {response}")
            
            # Attempt to parse JSON, with error handling
            try:
                agent_spec = json.loads(response)
            except json.JSONDecodeError:
                # If parsing fails, try to extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        agent_spec = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from response: {response}")
                        return None
                else:
                    logger.error(f"No valid JSON found in response: {response}")
                    return None
            
            # Validate required keys
            if not all(key in agent_spec for key in ['agent_name', 'description', 'capabilities']):
                logger.error(f"Incomplete agent specification: {agent_spec}")
                return None
            
            # Create the agent
            result = self.agent_manager.create_agent_with_ai(
                agent_spec["agent_name"], 
                agent_spec["description"], 
                ", ".join(agent_spec["capabilities"])
            )
            
            logger.info(f"🎉 {result}")
            
            # Reload agents
            self.agents = self.load_agents()
            
            # Return the new agent name
            return agent_spec["agent_name"]
        except Exception as e:
            logger.error(f"❌ Failed to create specialized agent: {e}")
            logger.error(f"Full error details: {traceback.format_exc()}")
            return None

    def route_task(self, task):
        method_start = time.time()
        logger.info(f"🚢 Routing task: {task}")
        
        # Special handling for explicit agent creation requests
        if task.lower().startswith(("create agent", "make agent", "generate agent")):
            logger.info("🤖 Explicit agent creation request detected")
            agent_name = self.create_specialized_agent(task)
            
            if agent_name:
                return f"✨ Successfully created new agent: {agent_name}"
            else:
                return "⚠️ Failed to create specialized agent"

        # Refined task selection
        refined_task = self.refine_task(task)
        agent_name = self.select_agent(refined_task)

        # If no suitable agent found, create one dynamically
        if not agent_name:
            logger.info("🔍 No suitable agent found, attempting to create a specialized agent")
            agent_name = self.create_specialized_agent(refined_task)
            
            # If we still don't have an agent, fall back to AI
            if not agent_name:
                logger.info("📝 Failed to create agent, falling back to AI.")
                fallback_response = self.llm_client.generate_response(refined_task)
                route_time = time.time() - method_start
                logger.debug(f"⏱️ Fallback task routing time: {route_time:.4f} seconds")
                return fallback_response

        # Fetch the actual agent instance
        agent = self.agent_manager.get_agent_instance(agent_name)
        if not agent:
            logger.error(f"❌ Failed to initialize agent: {agent_name}")
            return f"⚠️ Failed to initialize agent: {agent_name}"

        try:
            # Call the act method if it exists, otherwise use generate_response
            if hasattr(agent, 'act') and callable(getattr(agent, 'act')):
                response = agent.act(refined_task)
            else:
                response, _ = agent.generate_final_response(refined_task)
            
            self.agent_manager.update_agent_stats(agent_name, success=True)
            
            # Log total routing time
            route_time = time.time() - method_start
            logger.info(f"✅ Task routed successfully via {agent_name}")
            logger.debug(f"⏱️ Total task routing time: {route_time:.4f} seconds")
            
            return response
        except Exception as e:
            logger.error(f"⚠️ Agent execution failed: {e}")
            self.agent_manager.update_agent_stats(agent_name, success=False)
            route_time = time.time() - method_start
            logger.debug(f"⏱️ Failed task routing time: {route_time:.4f} seconds")
            return f"⚠️ Error executing task with {agent_name}: {str(e)}"