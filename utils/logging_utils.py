import logging
import os
import sys
import colorama
from typing import Optional
from tools.config_loader import load_config

# Initialize colorama for cross-platform color support
colorama.init()

# ANSI color codes optimized for dark terminal backgrounds
COLORS = {
    'RESET': '\033[0m',
    'INFO': '\033[38;5;39m',     # Light blue - easy on the eyes
    'DEBUG': '\033[38;5;245m',   # Medium gray - subtle but readable
    'WARNING': '\033[38;5;214m', # Amber - visible without being harsh
    'ERROR': '\033[38;5;196m',   # Red - stands out but not too bright
    'CRITICAL': '\033[48;5;196m\033[38;5;231m', # White on red background
    'TIME': '\033[38;5;245m',    # Medium gray for timestamps
    'NAME': '\033[38;5;149m'     # Soft green for logger names
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter adding color to log records based on level"""
    
    def format(self, record):
        # Store the original levelname
        levelname = record.levelname
        
        # Apply color to the level name
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        
        # Format the message
        message = super().format(record)
        
        # Replace timestamp and logger name with colored versions
        if hasattr(self, '_fmt') and '%(asctime)s' in self._fmt:
            message = message.replace(
                record.asctime, 
                f"{COLORS['TIME']}{record.asctime}{COLORS['RESET']}"
            )
        
        if hasattr(self, '_fmt') and '%(name)s' in self._fmt:
            colored_name = f"{COLORS['NAME']}{record.name}{COLORS['RESET']}"
            message = message.replace(record.name, colored_name)
            
        return message

class LoggingConfig:
    """Centralized logging configuration manager."""

    @staticmethod
    def setup_logging(
        logger_name: Optional[str] = None, 
        config_path: Optional[str] = None
    ) -> logging.Logger:
        """
        Configure logging based on config.toml settings
        
        Args:
            logger_name (str, optional): Specific logger to configure
            config_path (str, optional): Path to config.toml file
        
        Returns:
            logging.Logger: Configured logger
        """
        # Load config using the config loader
        config = load_config()
        
        # Determine log level from config
        debug_mode = config.get('debug', {}).get('debug_mode', False)
        logging_config = config.get('logging', {})
        
        # Default to DEBUG if debug_mode is True
        log_level = logging.DEBUG if debug_mode else logging.INFO
        
        # Override with explicit logging level if provided
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        config_level = logging_config.get('level', 'DEBUG').upper()
        log_level = level_map.get(config_level, log_level)
        
        # Logging format
        log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        date_format = '%H:%M:%S'
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        root_logger.handlers = []
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_formatter = ColoredFormatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
        
        # File logging if enabled - no colors in file
        if logging_config.get('to_file', False):
            logs_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                'logs'
            )
            os.makedirs(logs_dir, exist_ok=True)
            
            log_file = os.path.join(logs_dir, 'aetherflow.log')
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(log_format, date_format)
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
        
        # Create or get logger
        logger = logging.getLogger(logger_name) if logger_name else root_logger
        return logger

# Convenience function for quick import
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience method to get a configured logger
    
    Args:
        name (str, optional): Name of the logger
    
    Returns:
        logging.Logger: Configured logger
    """
    return LoggingConfig.setup_logging(name)