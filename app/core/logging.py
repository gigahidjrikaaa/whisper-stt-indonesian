"""
Logging configuration for the application.

This module sets up structured logging with appropriate formatters,
handlers, and log levels. It ensures consistent logging across all
modules and provides debugging capabilities.
"""

import logging
import sys
from typing import Optional

from .config import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure application logging.
    
    Sets up logging with appropriate format, level, and handlers.
    Ensures logs are written to both console and optionally to files.
    
    Args:
        log_level: Optional log level override. If not provided,
                  uses the level from settings.
    """
    settings = get_settings()
    level = log_level or settings.log_level
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Configure specific loggers
    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    
    # Enable detailed logging for our application
    app_logger = logging.getLogger("whisper_stt")
    app_logger.setLevel(getattr(logging, level.upper()))
    
    # Enable faster-whisper logging for debugging if needed
    if level.upper() == "DEBUG":
        logging.getLogger("faster_whisper").setLevel(logging.DEBUG)
    else:
        logging.getLogger("faster_whisper").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger, typically __name__ of the calling module
        
    Returns:
        Logger: Configured logger instance
    """
    return logging.getLogger(f"whisper_stt.{name}")


# Initialize logging when module is imported
setup_logging()
