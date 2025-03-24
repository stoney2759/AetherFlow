class BaseTool:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def run(self, *args, **kwargs):
        raise NotImplementedError("Tool must implement a run method.")
