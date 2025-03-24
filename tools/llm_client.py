import logging
import requests  # ✅ FIX: Import requests
from tools.config_loader import CONFIG

class LLMClient:
    """Handles API requests to an LLM provider."""

    def __init__(self, llm_config):
        """Initialize LLM client with configuration settings."""
        self.model = llm_config.get("model", "gpt-4o")
        self.base_url = llm_config.get("base_url", "").rstrip("/")  # ✅ Ensure no trailing slash
        self.api_key = llm_config.get("api_key", "")
        self.max_tokens = llm_config.get("max_tokens", 4096)
        self.temperature = llm_config.get("temperature", 0.2)

        # ✅ Debug Logging
        logging.debug(f"🛠️ LLMClient Loaded - Model: {self.model}, Base URL: {self.base_url}, API Key: {self.api_key[:5]}..., Tokens: {self.max_tokens}, Temp: {self.temperature}")

        # ✅ Ensure valid configuration
        if not self.base_url:
            logging.error("⚠️ LLMClient Error: Missing base_url in config.")
        if not self.api_key:
            logging.error("⚠️ LLMClient Error: No API key provided. Check 'config.toml'.")

    def generate_response(self, prompt: str) -> str:
        """Sends a request to the LLM API and returns a response."""
        if not self.api_key:
            logging.error("⚠️ LLMClient Error: No API key provided. Check 'config.toml'.")
            return "LLM Error: No API key provided."

        try:
            endpoint = f"{self.base_url}/chat/completions"
            logging.debug(f"🛠️ Sending request to LLM API: {endpoint}")

            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],  # ✅ FIX: Ensure correct API format
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            response = requests.post(endpoint, json=payload, headers=headers)  # ✅ FIX: Use requests
            response.raise_for_status()

            return response.json()["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logging.error(f"⚠️ LLMClient Error: {e}")
            return f"LLM Error: {str(e)}"
