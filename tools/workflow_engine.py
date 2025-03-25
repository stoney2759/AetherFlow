# tools/workflow_engine.py
import logging
import time
import json
import os
import re
from typing import Dict, List, Any, Callable, Optional
from tools.config_loader import CONFIG
from tools.agent_manager import AgentManager

class WorkflowEngine:
    """
    Manages collaborative workflows between multiple agents working on a complex task.
    Inspired by CrewAI's approach to agent collaboration.
    """
    
    def __init__(self, llm_client, config=None):
        self.llm_client = llm_client
        self.config = config or CONFIG
        self.agent_manager = AgentManager(llm_client, save_enabled=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.workspace = os.path.join(os.getcwd(), "workspace")
        os.makedirs(self.workspace, exist_ok=True)
        self.memory = {}
        self.workflow_history = []
        
    def create_workflow(self, project_name: str, goal: str):
        """
        Creates a new workflow with a defined goal and workspace.
        
        Args:
            project_name: Name of the project/workflow
            goal: The overall goal to be accomplished
            
        Returns:
            workflow_id: Identifier for the workflow
        """
        workflow_id = f"{project_name.lower().replace(' ', '_')}_{int(time.time())}"
        project_dir = os.path.join(self.workspace, workflow_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create workflow definition
        workflow = {
            "id": workflow_id,
            "name": project_name,
            "goal": goal,
            "status": "initialized",
            "created_at": time.time(),
            "updated_at": time.time(),
            "workspace": project_dir,
            "agents": [],
            "tasks": [],
            "artifacts": [],
            "current_stage": "planning",
            "memory": {}
        }
        
        # Save workflow definition
        with open(os.path.join(project_dir, "workflow.json"), 'w') as f:
            json.dump(workflow, f, indent=2)
            
        self.logger.info(f"✨ Created new workflow: {workflow_id} for '{project_name}'")
        return workflow_id
        
    def plan_workflow(self, workflow_id: str):
        """
        Plans the workflow by identifying required roles, tasks, and dependencies.
        
        Args:
            workflow_id: Identifier for the workflow
            
        Returns:
            plan: The workflow plan with roles and tasks
        """
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
            
        self.logger.info(f"🧠 Planning workflow: {workflow_id}")
        
        # Generate planning prompt
        planning_prompt = f"""
        You are a project manager planning a complex workflow. The goal is:
        
        {workflow['goal']}
        
        Please create a comprehensive workflow plan with the following elements:
        
        1. Required agent roles (3-6 specialized agents)
        2. Tasks for each agent role
        3. Task dependencies and sequence
        4. Data sharing requirements
        5. Success criteria
        
        Format your response as a valid JSON object with the following structure:
        {{
            "roles": [
                {{
                    "role": "role_name",
                    "description": "Description of role",
                    "capabilities": ["capability1", "capability2"],
                    "responsibilities": ["responsibility1", "responsibility2"]
                }}
            ],
            "tasks": [
                {{
                    "id": "task_1",
                    "name": "Task name",
                    "description": "Task description",
                    "assigned_to": "role_name",
                    "depends_on": ["task_id_1", "task_id_2"],
                    "expected_output": "Description of expected output"
                }}
            ],
            "workflow_sequence": ["task_1", "task_2", "task_3"],
            "success_criteria": ["criterion1", "criterion2"]
        }}
        
        Make sure the workflow is logically structured and will accomplish the goal.
        """
        
        try:
            plan_response = self.llm_client.generate_response(planning_prompt)
            self.logger.info(f"Received planning response of length: {len(plan_response)}")
            
            # Extract JSON from the response
            try:
                plan = json.loads(plan_response)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'(\{.*\})', plan_response, re.DOTALL)
                if json_match:
                    try:
                        plan = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse JSON from response: {plan_response[:200]}...")
                        return {"error": "Failed to parse workflow plan JSON"}
                else:
                    self.logger.error(f"No valid JSON found in planning response")
                    return {"error": "Invalid planning response format"}
            
            # Update workflow with plan
            workflow["roles"] = plan.get("roles", [])
            workflow["tasks"] = plan.get("tasks", [])
            workflow["workflow_sequence"] = plan.get("workflow_sequence", [])
            workflow["success_criteria"] = plan.get("success_criteria", [])
            workflow["current_stage"] = "agent_creation"
            workflow["updated_at"] = time.time()
            
            # Save updated workflow
            self._save_workflow(workflow)
            
            self.logger.info(f"📋 Created workflow plan with {len(workflow['roles'])} roles and {len(workflow['tasks'])} tasks")
            return plan
            
        except Exception as e:
            self.logger.error(f"❌ Workflow planning failed: {e}")
            return {"error": str(e)}
    
    def create_agents_for_workflow(self, workflow_id: str):
        """
        Creates specialized agents for each role in the workflow.
        
        Args:
            workflow_id: Identifier for the workflow
            
        Returns:
            agents: List of created agents
        """
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
            
        self.logger.info(f"🤖 Creating agents for workflow: {workflow_id}")
        
        created_agents = []
        
        for role in workflow.get("roles", []):
            role_name = role.get("role", "").lower().replace(" ", "_")
            agent_name = f"{role_name}_agent"
            
            # Check if agent already exists
            if agent_name in self.agent_manager.load_agents():
                self.logger.info(f"Agent {agent_name} already exists, reusing")
            else:
                # Create agent
                description = role.get("description", "")
                capabilities = ", ".join(role.get("capabilities", []))
                
                # Create agent with AI
                result = self.agent_manager.create_agent_with_ai(
                    agent_name,
                    description,
                    capabilities
                )
                
                self.logger.info(f"Agent creation result: {result}")
            
            # Add to workflow
            workflow["agents"].append({
                "name": agent_name,
                "role": role.get("role", ""),
                "description": role.get("description", ""),
                "capabilities": role.get("capabilities", []),
                "responsibilities": role.get("responsibilities", [])
            })
            
            created_agents.append(agent_name)
        
        # Update workflow
        workflow["current_stage"] = "execution"
        workflow["updated_at"] = time.time()
        self._save_workflow(workflow)
        
        self.logger.info(f"✅ Created {len(created_agents)} agents for workflow")
        return created_agents
    
    def execute_workflow(self, workflow_id: str, max_iterations=10):
        """
        Executes the workflow by assigning tasks to agents and handling their outputs.
        
        Args:
            workflow_id: Identifier for the workflow
            max_iterations: Maximum number of task execution iterations
            
        Returns:
            results: The final workflow results
        """
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
            
        self.logger.info(f"🚀 Executing workflow: {workflow_id}")
        
        # Track task status
        task_status = {task["id"]: "pending" for task in workflow["tasks"]}
        
        # Initialize workflow memory
        memory = workflow.get("memory", {})
        
        # Initialize artifacts list
        artifacts = []
        
        # Execute tasks in sequence
        for i, task_id in enumerate(workflow.get("workflow_sequence", [])):
            if i >= max_iterations:
                self.logger.warning(f"⚠️ Reached maximum iterations ({max_iterations}), stopping workflow")
                break
                
            # Find task
            task = next((t for t in workflow["tasks"] if t["id"] == task_id), None)
            if not task:
                self.logger.error(f"❌ Task {task_id} not found in workflow")
                continue
                
            # Check dependencies
            dependencies = task.get("depends_on", [])
            if any(task_status.get(dep_id) != "completed" for dep_id in dependencies):
                self.logger.warning(f"⚠️ Dependencies not met for task {task_id}, skipping")
                continue
                
            # Find agent
            role = task.get("assigned_to")
            agent_name = next((a["name"] for a in workflow["agents"] if a["role"] == role), None)
            if not agent_name:
                self.logger.error(f"❌ No agent found for role {role}")
                continue
                
            # Get agent instance
            agent = self.agent_manager.get_agent_instance(agent_name)
            if not agent:
                self.logger.error(f"❌ Failed to initialize agent {agent_name}")
                continue
                
            # Prepare task context with memory from previous tasks
            task_context = {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "task_name": task.get("name", ""),
                "task_description": task.get("description", ""),
                "workspace": workflow["workspace"],
                "memory": memory,
                "artifacts": artifacts
            }
            
            # Execute task
            self.logger.info(f"⚙️ Executing task {task_id} with agent {agent_name}")
            try:
                # Create a task prompt with context
                task_prompt = self._create_task_prompt(task, task_context)
                
                # Execute task with agent
                if hasattr(agent, 'act') and callable(getattr(agent, 'act')):
                    result = agent.act(task_prompt)
                else:
                    result, _ = agent.generate_final_response(task_prompt)
                
                self.logger.info(f"Task result type: {type(result)}")
                if isinstance(result, str):
                    self.logger.info(f"Task result (first 100 chars): {result[:100]}...")
                else:
                    self.logger.info(f"Task result structure: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                
                # Parse task result
                task_result = self._parse_task_result(result)
                
                # Update memory with task result
                memory[task_id] = task_result.get("output", {})
                
                # Update artifacts
                if "artifacts" in task_result:
                    self.logger.info(f"Found {len(task_result.get('artifacts', []))} artifacts in task result")
                    for artifact in task_result.get("artifacts", []):
                        # Enhanced logging for artifact saving
                        filename = artifact.get("filename", "")
                        if not filename:
                            self.logger.warning(f"Artifact missing filename: {artifact.get('name', 'unnamed')}")
                            continue
                            
                        artifact_path = os.path.join(workflow["workspace"], filename)
                        self.logger.info(f"Attempting to save artifact to: {artifact_path}")
                        
                        try:
                            content = artifact.get("content", "")
                            self.logger.info(f"Artifact content length: {len(content)}")
                            
                            # Create directory if needed
                            os.makedirs(os.path.dirname(os.path.abspath(artifact_path)), exist_ok=True)
                            
                            with open(artifact_path, "w", encoding="utf-8") as f:
                                f.write(content)
                                
                            self.logger.info(f"✅ Successfully saved artifact to: {artifact_path}")
                            
                            artifacts.append({
                                "name": artifact.get("name", ""),
                                "description": artifact.get("description", ""),
                                "filename": filename,
                                "created_by": agent_name,
                                "created_at": time.time()
                            })
                        except Exception as e:
                            self.logger.error(f"❌ Failed to save artifact to {artifact_path}: {e}")
                
                # Update task status
                task_status[task_id] = "completed"
                
                # Record in workflow history
                self.workflow_history.append({
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "agent": agent_name,
                    "timestamp": time.time(),
                    "status": "completed",
                    "message": f"Task {task_id} completed by {agent_name}"
                })
                
                # Update agent stats
                self.agent_manager.update_agent_stats(agent_name, success=True)
                
            except Exception as e:
                task_status[task_id] = "failed"
                self.logger.error(f"❌ Task execution failed: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Record in workflow history
                self.workflow_history.append({
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "agent": agent_name,
                    "timestamp": time.time(),
                    "status": "failed",
                    "message": f"Task {task_id} failed: {str(e)}"
                })
                
                # Update agent stats
                self.agent_manager.update_agent_stats(agent_name, success=False)
        
        # Update workflow status
        if all(status == "completed" for status in task_status.values()):
            workflow["status"] = "completed"
        else:
            workflow["status"] = "partial"
            
        # Update workflow
        workflow["memory"] = memory
        workflow["artifacts"] = artifacts
        workflow["updated_at"] = time.time()
        self._save_workflow(workflow)
        
        # Generate final summary
        return self._generate_workflow_summary(workflow_id)
    
    def process_user_feedback(self, workflow_id: str, feedback: str):
        """
        Processes user feedback and updates the workflow accordingly.
        
        Args:
            workflow_id: Identifier for the workflow
            feedback: User feedback for the workflow results
            
        Returns:
            updated_plan: The updated workflow plan
        """
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
            
        self.logger.info(f"📝 Processing user feedback for workflow: {workflow_id}")
        
        # Generate feedback analysis prompt
        feedback_prompt = f"""
        You are analyzing user feedback for a workflow project with the goal:
        
        {workflow['goal']}
        
        Current project artifacts:
        {json.dumps(workflow.get('artifacts', []), indent=2)}
        
        User feedback:
        {feedback}
        
        Please analyze the feedback and create an update plan with the following elements:
        
        1. What changes are needed based on the feedback?
        2. Which tasks need to be re-executed?
        3. Are any new tasks needed?
        
        Format your response as a valid JSON object with the following structure:
        {{
            "analysis": "Brief analysis of the feedback",
            "changes_needed": ["change1", "change2"],
            "tasks_to_update": ["task_id_1", "task_id_2"],
            "new_tasks": [
                {{
                    "id": "new_task_1",
                    "name": "New task name",
                    "description": "New task description",
                    "assigned_to": "role_name",
                    "depends_on": ["task_id_1"],
                    "expected_output": "Description of expected output"
                }}
            ]
        }}
        """
        
        try:
            feedback_response = self.llm_client.generate_response(feedback_prompt)
            
            # Extract JSON from the response
            try:
                update_plan = json.loads(feedback_response)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'(\{.*\})', feedback_response, re.DOTALL)
                if json_match:
                    try:
                        update_plan = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse JSON from feedback response: {feedback_response[:200]}...")
                        return {"error": "Failed to parse feedback response JSON"}
                else:
                    self.logger.error(f"No valid JSON found in feedback response")
                    return {"error": "Invalid feedback response format"}
            
            # Add new tasks to workflow
            if "new_tasks" in update_plan:
                workflow["tasks"].extend(update_plan.get("new_tasks", []))
                
                # Update workflow sequence
                for new_task in update_plan.get("new_tasks", []):
                    workflow["workflow_sequence"].append(new_task["id"])
            
            # Mark tasks for re-execution
            task_status = {task["id"]: "pending" for task in workflow["tasks"] 
                          if task["id"] in update_plan.get("tasks_to_update", [])}
            
            # Set workflow to execution stage
            workflow["current_stage"] = "feedback_execution"
            workflow["updated_at"] = time.time()
            
            # Save user feedback
            if "feedback_history" not in workflow:
                workflow["feedback_history"] = []
                
            workflow["feedback_history"].append({
                "feedback": feedback,
                "analysis": update_plan.get("analysis", ""),
                "timestamp": time.time()
            })
            
            # Save updated workflow
            self._save_workflow(workflow)
            
            # Execute updated workflow
            if update_plan.get("tasks_to_update") or update_plan.get("new_tasks"):
                self.execute_workflow(workflow_id)
                
            return update_plan
            
        except Exception as e:
            self.logger.error(f"❌ Feedback processing failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def _create_task_prompt(self, task, context):
        """Creates a detailed prompt for a task with context."""
        prompt = f"""
        # Task Assignment: {task.get('name', '')}
        
        ## Task Description
        {task.get('description', '')}
        
        ## Expected Output
        {task.get('expected_output', '')}
        
        ## Workspace Information
        - Working directory: {context.get('workspace')}
        
        ## Available Memory
        {json.dumps(context.get('memory', {}), indent=2)}
        
        ## Available Artifacts
        {json.dumps(context.get('artifacts', []), indent=2)}
        
        ## Instructions
        1. Complete the task based on the description and expected output
        2. You can access information from previous tasks using the memory
        3. You can create artifacts (files) in the workspace
        4. Format your response to include:
           - A summary of what you did
           - Any outputs or results
           - Any artifacts you created
        
        Please focus solely on your assigned task. Structure your response in JSON format with:
        {{
            "output": {{
                "summary": "Summary of what you did",
                "result": "Your task results"
            }},
            "artifacts": [
                {{
                    "name": "artifact_name",
                    "description": "Brief description",
                    "filename": "filename.ext",
                    "content": "The full content of the file"
                }}
            ]
        }}
        """
        return prompt
    
    def _parse_task_result(self, result):
        """Attempts to parse task result as JSON."""
        try:
            # If result is already a dictionary, return it
            if isinstance(result, dict):
                return result
                
            # Try to find JSON in the response
            json_matches = re.findall(r'```json\s*(.*?)\s*```|(\{.*\})', result, re.DOTALL)
            for match in json_matches:
                for group in match:
                    if group and "{" in group:
                        try:
                            parsed = json.loads(group)
                            return parsed
                        except json.JSONDecodeError:
                            continue
            
            # If no JSON found, try to parse the whole response
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If parsing fails, return structured format of raw response
                return {
                    "output": {
                        "summary": "Task completed but returned unstructured response",
                        "result": result
                    },
                    "artifacts": []
                }
        except Exception as e:
            self.logger.error(f"Error parsing task result: {e}")
            # If all parsing fails, return a minimal structure
            return {
                "output": {
                    "summary": "Error parsing task response",
                    "result": str(result)[:1000] if result else "No result"
                },
                "artifacts": []
            }
    
    def _generate_workflow_summary(self, workflow_id):
        """Generates a summary of the workflow results."""
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
            
        artifacts = workflow.get("artifacts", [])
        memory = workflow.get("memory", {})
        
        # Create a more detailed summary
        summary = {
            "workflow_id": workflow_id,
            "name": workflow.get("name", ""),
            "goal": workflow.get("goal", ""),
            "status": workflow.get("status", ""),
            "created_at": workflow.get("created_at", 0),
            "updated_at": workflow.get("updated_at", 0),
            "artifacts": [
                {
                    "name": artifact.get("name", ""),
                    "description": artifact.get("description", ""),
                    "filename": artifact.get("filename", ""),
                    "created_by": artifact.get("created_by", ""),
                    "full_path": os.path.join(workflow.get("workspace", ""), artifact.get("filename", ""))
                }
                for artifact in artifacts
            ],
            "task_results": {
                task_id: memory.get(task_id, {}).get("summary", "No summary available") 
                for task_id in workflow.get("workflow_sequence", [])
                if task_id in memory
            },
            "memory": memory,  # Include full memory for debugging
            "workspace": workflow.get("workspace", "")  # Include workspace path
        }
        
        # Save summary artifact
        summary_path = os.path.join(workflow["workspace"], "workflow_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
            
        return summary
    
    def _load_workflow(self, workflow_id):
        """Loads workflow data from file."""
        try:
            workflow_path = os.path.join(self.workspace, workflow_id, "workflow.json")
            if not os.path.exists(workflow_path):
                self.logger.error(f"Workflow file not found: {workflow_path}")
                return None
                
            with open(workflow_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {e}")
            return None
    
    def _save_workflow(self, workflow):
        """Saves workflow data to file."""
        try:
            workflow_id = workflow.get("id")
            workflow_path = os.path.join(self.workspace, workflow_id, "workflow.json")
            
            with open(workflow_path, 'w') as f:
                json.dump(workflow, f, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow: {e}")
            return False