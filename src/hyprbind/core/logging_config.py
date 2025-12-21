"""Logging configuration for HyprBind.

This module provides structured logging setup to replace scattered print()
statements. Logging enables proper debug output, error tracking, and
production-ready observability.
"""

__all__ = ["setup_logging", "get_logger", "DEFAULT_FORMAT", "DEBUG_FORMAT"]

import logging
import sys
from typing import Optional

# Default format for production
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Debug format with line numbers for development
DEBUG_FORMAT = '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    debug: bool = False
) -> None:
    """Configure logging for the HyprBind application.

    This should be called once at application startup, before any loggers
    are used.

    Args:
        level: Logging level (default INFO). Use logging.DEBUG for verbose output.
        log_file: Optional file path to write logs to (in addition to stderr).
        debug: If True, use detailed format with line numbers.

    Example:
        >>> setup_logging(level=logging.DEBUG, debug=True)
        >>> logger = get_logger(__name__)
        >>> logger.debug("Application starting")
    """
    fmt = DEBUG_FORMAT if debug else DEFAULT_FORMAT

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Reduce noise from GTK/GLib internals
    logging.getLogger('gi').setLevel(logging.WARNING)
    logging.getLogger('gi.repository').setLevel(logging.WARNING)

    # Log that we're configured
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialized at level %s", logging.getLevelName(level))


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    This is a convenience wrapper around logging.getLogger that ensures
    consistent logger naming.

    Args:
        name: Usually __name__ of the calling module

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Config loaded successfully")
    """
    return logging.getLogger(name)
