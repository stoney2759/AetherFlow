Here's the raw markdown formatted version of the corrected README.md for easy copying and pasting:

```markdown
# AetherFlow

AetherFlow is a modular framework for orchestrating AI agents with task routing, planning capabilities, and extensible tools. Designed for seamless agent collaboration and workflow automation.

## Features

- **Agent Orchestration**: Coordinate multiple AI agents working together on complex tasks
- **Task Routing System**: Intelligent distribution of tasks to specialized agents
- **Planning Capabilities**: Agents with planning abilities to break down complex problems
- **Extensible Tool Framework**: Easily integrate new capabilities through a flexible tool system
- **Configuration Management**: Simple TOML-based configuration

## Project Structure

```
AetherFlow/
├── agents/                 # Agent implementations
│   ├── agent_core.py       # Core agent functionality
│   ├── agent_creator_agent.py
│   ├── agent_template.py   # Template for creating new agents
│   ├── planning_agent.py   # Specialized planning capabilities
│   ├── prompt_generator_agent.py
│   ├── task_router.py      # Handles task distribution
│   └── worker_agent.py     # Task execution agents
├── config/                 # Configuration files
│   ├── agents_index.json   # Registry of available agents
│   └── example_config.toml # Example configuration (see config setup)
├── tasks/                  # Task management
│   └── task_queue.py       # Queue system for task processing
├── tools/                  # Tool implementations
│   ├── agent_manager.py    # Manages agent lifecycle
│   ├── api_tool.py         # API integration tools
│   ├── base_tool.py        # Base class for all tools
│   ├── config_loader.py    # Configuration management
│   └── llm_client.py       # LLM integration
├── utils/
│   └── logging_utils.py    # Logging utilities
└── main.py                 # Application entry point
```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/stoney2759/AetherFlow.git
   cd AetherFlow
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create your configuration:
   ```
   cp config/example_config.toml config/config.toml
   ```

4. Edit `config/config.toml` with your settings

## Usage

Run the main application:
```
python main.py
```

## Creating New Agents

- Use the agent template in **agents/agent_template.py** as a starting point
- Register your new agent in **config/agents_index.json**
- Configure your agent in **config/config.toml**

## Extending with New Tools

- Subclass **base_tool.py** to create new capabilities
- Register your tool with the appropriate agents

## Configuration

Configuration is handled through TOML files. See **config/example_config.toml** for a complete example.

```
[api]
provider = "openai"
api_key = "your_api_key_here"

[agents]
# Agent-specific configurations
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
```

You can simply copy this entire block and paste it into your README.md file. The formatting will display correctly on GitHub.