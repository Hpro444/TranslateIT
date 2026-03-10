"""
Logging Module

This module provides centralized logging configuration for the TranslateIt application.
It sets up both console and file logging handlers with configurable settings from the
Configuration singleton.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from project.config import Configuration

_logger_instance: Optional[logging.Logger] = None


def setup_logger() -> logging.Logger:
    """
    Set up and configure the application logger.

    Creates a logger with console and optional file handlers based on
    configuration settings. Uses rotating file handler to manage log file sizes.

    Returns:
        logging.Logger: Configured logger instance.
    """
    global _logger_instance

    if _logger_instance is not None:
        return _logger_instance

    config = Configuration()

    # Create logger
    logger = logging.getLogger("translateit")
    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    logger.propagate = False

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(config.log_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if enabled)
    if config.enable_file_logging:
        # Create logs directory if it doesn't exist
        os.makedirs(config.logs_dir, exist_ok=True)

        log_file = os.path.join(config.logs_dir, "translateit.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.log_max_bytes,
            backupCount=config.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the application logger instance.

    If the logger hasn't been set up yet, this will initialize it.

    Returns:
        logging.Logger: The configured logger instance.
    """
    if _logger_instance is None:
        return setup_logger()
    return _logger_instance
