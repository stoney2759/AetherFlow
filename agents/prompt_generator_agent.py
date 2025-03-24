import time
import logging
from agents.agent_core import AgentCore
from tools.config_loader import CONFIG

# Load Debug Mode
DEBUG_MODE = CONFIG.get("debug", {}).get("debug_mode", False)

class PromptGeneratorAgent(AgentCore):
    """AI agent that refines user input and generates a final AI response."""

    def __init__(self, llm_client, config=None):
        super().__init__(llm_client, config)
        if DEBUG_MODE:
            self.logger.debug("PromptGeneratorAgent initialized with debug mode ON.")

    def refine_prompt(self, user_input: str) -> str:
        """Uses AI to improve the user's prompt before sending it for processing."""
        self.logger.info(f"Refining AI prompt for input: {user_input}")

        system_instruction = (

            "You are an AI assistant skilled in prompt engineering. "
            "If the user is asking for a prompt about something, maintain that meta-level intent. "
            "Don't convert 'create a prompt about X' into just 'create X'. "
            "Rewrite the user's raw input into a well-structured AI prompt."    
            " Ensure clarity, specificity, and context-awareness."
            " Format it properly using bullet points or numbered lists where appropriate."
            " Do NOT provide any response to the prompt, just rewrite the prompt itself."
        )

        try:
            refined_prompt = self.llm_client.generate_response(
                f"{system_instruction}\n\nUser Input: {user_input}\n\nRefined Prompt:"
            )
            self.logger.info(f"Prompt refined successfully.")
            return refined_prompt.strip()
        except Exception as e:
            self.logger.error(f"Prompt refinement failed: {e}")
            return user_input  # Fall back to original input if AI fails

    def generate_final_response(self, user_input: str) -> tuple[str, float]:
        """Refines the prompt, sends it to AI, and returns the response."""
        if not user_input.strip():
            return "Error: The input is empty.", 0.0

        self.logger.info(f"Generating final AI response for input: {user_input}")
        start_time = time.time()

        try:
            # Step 1: Refine the prompt
            refined_prompt = self.refine_prompt(user_input)

            # Step 2: Generate AI response from refined prompt
            final_response = self.llm_client.generate_response(refined_prompt)
            elapsed_time = time.time() - start_time

            self.logger.info(f"Final AI response generated in {elapsed_time:.2f} seconds.")
            return final_response.strip(), elapsed_time
        except Exception as e:
            self.logger.error(f"Final AI response failed: {e}")
            return f"Error: {str(e)}", 0.0
        
    def act(self, task):
        """Acts on the given task by generating a final response."""
        self.logger.info(f"PromptGeneratorAgent handling task: {task}")
        response, _ = self.generate_final_response(task)
        return response