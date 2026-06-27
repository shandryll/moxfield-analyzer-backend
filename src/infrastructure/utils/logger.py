"""
Centralized logging configuration for the application.
Automatically configures based on ENVIRONMENT variable.
"""
import os
import sys
from loguru import logger

ENV = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if ENV == "development" else "INFO")

# Remove default handler
logger.remove()

if ENV == "production":
    # Production: Structured JSON logging to stdout (for container log aggregation)
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=True,
    )
else:
    # Development: Colorized console output
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level=LOG_LEVEL,
        colorize=True,
    )


def get_logger():
    """Get the configured logger instance."""
    return logger

