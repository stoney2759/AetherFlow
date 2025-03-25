import toml
import logging
import sys
import os
import json
from tools.llm_client import LLMClient
from agents.task_router import TaskRouter
from tools.config_loader import CONFIG
from tools.workflow_engine import WorkflowEngine
from utils.logging_utils import get_logger

# Load Debug Mode from config
DEBUG_MODE = CONFIG.get("debug", {}).get("debug_mode", False)

# Set up logging
logger = get_logger("Main")

# Force UTF-8 encoding for logging on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load configuration from TOML file
with open("config/config.toml", "r") as f:
    config = toml.load(f)

# Extract LLM settings dynamically
llm_config = config.get("llm", {})
model_name = llm_config.get("model", "gpt-4o")  
base_url = llm_config.get("base_url", "").strip()  
api_key = llm_config.get("api_key", "").strip()
max_tokens = llm_config.get("max_tokens", 4096)  
temperature = llm_config.get("temperature", 0.0)  

# Initialize LLMClient properly
llm_client = LLMClient(llm_config)

# Initialize Task Router
task_router = TaskRouter(llm_client)

# Initialize Workflow Engine
workflow_engine = WorkflowEngine(llm_client)

# Log the loaded configuration
logger.info("AetherFlow system initialized.")

def handle_workflow_command(user_input):
    """Handles workflow-specific commands."""
    if user_input.lower().startswith("workflow create"):
        # Extract goal from input
        goal = user_input[len("workflow create"):].strip()
        if not goal:
            return "Please provide a goal for the workflow."
            
        # Create a project name based on the goal
        project_name = "Project_" + "_".join(goal.split()[:3])
        
        # Create workflow
        workflow_id = workflow_engine.create_workflow(project_name, goal)
        
        # Plan workflow
        plan = workflow_engine.plan_workflow(workflow_id)
        
        # Create agents
        agents = workflow_engine.create_agents_for_workflow(workflow_id)
        
        # Execute workflow
        results = workflow_engine.execute_workflow(workflow_id)
        
        # Enhance the workflow result display
        if isinstance(results, dict) and "memory" in results:
            # Print memory details for debugging
            memory_info = "\n".join([f"{k}: {v.get('summary', 'No summary')[:100]}..." 
                                   for k, v in results.get("memory", {}).items()])
            print(f"\nDebug - Task Memory:\n{memory_info}")
            
            # Print workspace path for easy access to files
            if "workspace" in results:
                print(f"\nWorkspace directory: {results['workspace']}")
        
        # Create artifacts list if available
        artifacts_list = ""
        if results.get("artifacts"):
            artifacts_list = "\n".join([f"- {a.get('name', 'Unnamed')}: {a.get('full_path', a.get('filename', 'No file'))}" 
                                      for a in results.get("artifacts", [])])
        
        return f"""
        ✨ Workflow created and executed for: {goal}
        
        Workflow ID: {workflow_id}
        Status: {results.get('status', 'Unknown')}
        
        Created artifacts:
        {artifacts_list if artifacts_list else "No artifacts created"}
        
        Workspace directory: {results.get('workspace', 'Unknown')}
        
        Summary: 
        {results.get('summary', 'No summary available')}
        
        To provide feedback, use: "workflow feedback {workflow_id} your feedback here"
        """
        
    elif user_input.lower().startswith("workflow feedback"):
        # Extract workflow ID and feedback
        parts = user_input[len("workflow feedback"):].strip().split(" ", 1)
        if len(parts) < 2:
            return "Please provide both workflow ID and feedback."
            
        workflow_id = parts[0]
        feedback = parts[1]
        
        # Process feedback
        result = workflow_engine.process_user_feedback(workflow_id, feedback)
        
        if isinstance(result, dict) and "error" in result:
            return f"Error: {result['error']}"
        
        # Format changes if available
        changes_text = "No changes specified"
        if isinstance(result, dict) and "changes_needed" in result and result["changes_needed"]:
            changes = result.get("changes_needed", [])
            changes_text = "\n".join([f"- {change}" for change in changes])
        
        return f"""
        ✅ Feedback processed for workflow: {workflow_id}
        
        Analysis: {result.get('analysis', 'No analysis provided')}
        
        Changes requested:
        {changes_text}
        
        The workflow has been updated based on your feedback.
        """
        
    elif user_input.lower().startswith("workflow list"):
        # List all workflows in workspace directory
        workflow_dir = workflow_engine.workspace
        workflows = []
        
        if os.path.exists(workflow_dir):
            for d in os.listdir(workflow_dir):
                workflow_file = os.path.join(workflow_dir, d, "workflow.json")
                if os.path.exists(workflow_file):
                    try:
                        with open(workflow_file, 'r') as f:
                            workflow = json.load(f)
                        workflows.append({
                            "id": workflow.get("id", d),
                            "name": workflow.get("name", "Unnamed"),
                            "goal": workflow.get("goal", "No goal specified"),
                            "status": workflow.get("status", "unknown"),
                            "updated_at": workflow.get("updated_at", 0),
                            "workspace": workflow.get("workspace", "Unknown")
                        })
                    except Exception as e:
                        if DEBUG_MODE:
                            logger.debug(f"Error loading workflow {d}: {e}")
                        pass
                    
        if not workflows:
            return "No workflows found."
            
        workflows_list = "\n".join([
            f"- {w['id']}: {w['name']} - {w['status'].upper()} - {w['goal'][:50]}...\n  Directory: {w['workspace']}" 
            for w in workflows
        ])
        
        return f"""
        📋 Available Workflows:
        
        {workflows_list}
        
        Use "workflow feedback <id> <feedback>" to provide feedback on a workflow.
        Use "open <directory>" to view the workflow files.
        """
        
    elif user_input.lower().startswith("workflow open"):
        # Extract workflow ID
        workflow_id = user_input[len("workflow open"):].strip()
        if not workflow_id:
            return "Please provide a workflow ID to open."
            
        # Get workflow
        workflow = workflow_engine._load_workflow(workflow_id)
        if not workflow:
            return f"Workflow {workflow_id} not found."
            
        # Open the workflow directory
        workspace = workflow.get("workspace", "")
        if not workspace or not os.path.exists(workspace):
            return f"Workspace directory for workflow {workflow_id} not found."
            
        try:
            if sys.platform == 'win32':
                os.startfile(workspace)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.run(['open', workspace])
            else:  # Linux
                import subprocess
                subprocess.run(['xdg-open', workspace])
                
            return f"Opened workspace directory for workflow {workflow_id}."
        except Exception as e:
            return f"Error opening workspace directory: {str(e)}"
    
    return "Unknown workflow command. Available commands: workflow create, workflow feedback, workflow list, workflow open"

def main():
    print("\n🌟 Welcome to AetherFlow - Collaborative AI Agent System")
    print("----------------------------------------------------")
    print("Commands:")
    print("  - workflow create <goal>: Create a new collaborative workflow")
    print("  - workflow feedback <id> <feedback>: Provide feedback on a workflow")
    print("  - workflow list: List all available workflows")
    print("  - workflow open <id>: Open the workflow directory")
    print("  - Exit with 'quit', 'exit', or press Enter with empty input")
    print("----------------------------------------------------")
    
    empty_count = 0  # Track empty inputs
    
    while True:
        user_input = input("\n📝 Enter a request: ").strip()
        
        if not user_input:
            empty_count += 1
            if empty_count >= 1:  # Exit after 1 empty input
                print("👋 Goodbye!")
                break
            print("Press Enter again to exit.")
            continue
        else:
            empty_count = 0  # Reset on non-empty input
            
        if user_input.lower() in ['quit', 'exit']:
            print("👋 Goodbye!")
            break
            
        try:
            # Check if this is a workflow command
            if user_input.lower().startswith("workflow"):
                response = handle_workflow_command(user_input)
            else:
                # Regular task routing
                response = task_router.route_task(user_input)
                
            print(f"\n🤖 AI Response:\n----------------------\n{response}")
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            print(f"\n⚠️ Error: {str(e)}")
            if DEBUG_MODE:
                import traceback
                traceback_str = traceback.format_exc()
                logger.debug(f"Detailed error: {traceback_str}")
                print(f"\nDetailed error:\n{traceback_str}")

if __name__ == "__main__":
    main()