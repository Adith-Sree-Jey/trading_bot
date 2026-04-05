"""Centralized logging setup for the trading bot CLI."""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging() -> logging.Logger:
    """Configure root logger with rotating file + console handlers. Call once at CLI startup.

    Creates the logs directory if needed. File handler: DEBUG, 5MB x 3 backups.
    Console handler: INFO.

    Returns:
        The root logger.
    """
    from config import LOG_FILE, LOG_LEVEL_CONSOLE, LOG_LEVEL_FILE

    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL_FILE, logging.DEBUG))
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL_CONSOLE, logging.INFO))
    console_handler.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return root
