"""Logging utility for VHS Coffeeman project."""

import logging
import sys
from typing import Optional

# Configure default logging
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO

def setup_logger(name: str, level: Optional[int] = None, format_str: Optional[str] = None) -> logging.Logger:
    """Set up and return a logger with the given name.
    
    Args:
        name: Name of the logger, typically __name__
        level: Logging level (default: INFO)
        format_str: Log format string (default: timestamp - name - level - message)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(level or DEFAULT_LOG_LEVEL)
    
    # Create handler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level or DEFAULT_LOG_LEVEL)
    
    # Create formatter
    formatter = logging.Formatter(format_str or DEFAULT_LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Set up the root logger to handle uncaught exceptions and general logs
def setup_root_logger(level: int = logging.INFO, 
                      log_file: Optional[str] = None) -> logging.Logger:
    """Set up the root logger with console and optional file output.
    
    Args:
        level: Logging level
        log_file: Optional path to log file
        
    Returns:
        logging.Logger: Configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]: 
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger