import toml
import os
import logging

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/config.toml")

def load_config():
    """Loads the configuration from config.toml and logs values for debugging."""
    try:
        with open(CONFIG_PATH, "r") as file:
            config = toml.load(file)
        
        # ✅ Log loaded values for debugging
        logging.debug(f"🛠️ Loaded Config: {config}")
        return config
    except Exception as e:
        logging.error(f"⚠️ Error loading config: {e}")
        return {}

# Load config globally
CONFIG = load_config()