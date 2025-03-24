import toml
import logging
import sys
from tools.llm_client import LLMClient
from agents.task_router import TaskRouter
from tools.config_loader import CONFIG

# Load Debug Mode from config
DEBUG_MODE = CONFIG.get("debug", {}).get("debug_mode", False)

# Set up logging based on debug mode
if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Force UTF-8 encoding for logging on Windows
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

# Extract other configurations
logging_config = config.get("logging", {})

# Setup logging
log_level_str = logging_config.get("level", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

handlers = [logging.StreamHandler()]
if logging_config.get("to_file"):
    handlers.append(logging.FileHandler("logs/agent.log", mode="w", encoding="utf-8"))

logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
logger = logging.getLogger("AgentFramework")

# Log the loaded configuration
logger.info("Logging configured.")
logger.info(f"LLM Config: model={model_name}, base_url={base_url}, max_tokens={max_tokens}, temperature={temperature}")

if DEBUG_MODE:
    logger.info(f"Loaded API Key: {repr(api_key)} (Length: {len(api_key)})")

# Ensure API Key and Base URL are set properly
if not api_key or api_key.isspace():
    logger.warning("WARNING: No API key found in config. Update 'config/config.toml'.")
elif len(api_key) < 40:  # OpenAI keys are ~51 chars
    logger.warning("WARNING: API key is too short. Check 'config/config.toml'.")
else:
    logger.info("✅ API Key appears valid.")
    if DEBUG_MODE:
        logger.info(f"Loaded API Key: {repr(api_key)} (Length: {len(api_key)})")

# Initialize Task Router
task_router = TaskRouter(llm_client)

if DEBUG_MODE:
    logging.debug("🛠️ Debug mode is ON.")

# Get user input
user_input = input("\n📝 Enter a request: ").strip()

if user_input:
    if DEBUG_MODE:
        print("\n🛠️ [DEBUG] Routing task through TaskRouter...")

    final_response = task_router.route_task(user_input)

    if DEBUG_MODE:
        print("\n🛠️ [DEBUG] Task routing complete. AI-generated response follows:")

    print(f"\n🤖 AI Response:\n----------------------\n{final_response}")
else:
    print("⚠️ No input provided. Exiting...")