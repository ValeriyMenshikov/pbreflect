"""Logging configuration for the REST code generator."""

from __future__ import annotations

import sys
from enum import Enum

import loguru
from pydantic_settings import BaseSettings


class LogLevelEnum(str, Enum):
    """Enum for log levels supported by the logger."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LoggerSettings(BaseSettings):
    """Settings for configuring the logger behavior.

    Attributes:
        log_json: Whether to output logs in JSON format
        log_level: The minimum log level to display
    """

    log_json: bool = True
    log_level: LogLevelEnum = LogLevelEnum.DEBUG

    class Config:
        """Pydantic configuration."""

        env_prefix = "RESTCODEGEN_LOG_"


def build_root_logger(log_settings: LoggerSettings | None = None) -> loguru.Logger:
    """Build and configure the root logger.

    Args:
        log_settings: Optional logger settings, uses defaults if not provided

    Returns:
        Configured loguru Logger instance
    """
    # Use default settings if none provided
    log_settings = log_settings or LoggerSettings()

    # Remove default handlers
    loguru.logger.remove()

    # Configure logger based on settings
    if log_settings.log_json:
        loguru.logger.add(
            sys.stdout,
            level=log_settings.log_level.value,
            backtrace=False,
            diagnose=False,
            serialize=False,
        )
    else:
        loguru.logger.add(
            sys.stdout,
            level=log_settings.log_level.value,
        )

    return loguru.logger


# Global logger instance
LOGGER = build_root_logger()


def get_logger(name: str) -> loguru.Logger:
    """Get a named logger that includes the component name in logs.

    Args:
        name: Name of the component using the logger

    Returns:
        Logger instance with the component name bound to it
    """
    return loguru.logger.bind(logger_name=name)
