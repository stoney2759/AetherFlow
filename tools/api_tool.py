import requests
from .base_tool import BaseTool

class APITool(BaseTool):
    def run(self, endpoint: str, params: dict = None) -> dict:
        base_url = self.config.get("base_url", "")
        api_key = self.config.get("api_key", "")
        timeout = self.config.get("timeout", 30)
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        url = base_url + endpoint
        response = requests.get(url, params=params or {}, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
