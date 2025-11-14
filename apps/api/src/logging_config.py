"""Logging configuration for the resume bot."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from loguru import logger

# Constants
LOG_DIR: Final[Path] = Path("log")
LOG_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure loguru logger
logger.remove()  # Remove default handler

# Console sink
logger.add(
    sink=lambda msg: print(msg, end=""),  # Print to console
    format=LOG_FORMAT,
    level="DEBUG",
)

# File sink
logger.add(
    str(LOG_DIR / "resume-bot.log"),
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="20 MB",
    retention=1,
    encoding="utf-8",
    enqueue=True,
)

# Export logger for use in other modules
__all__ = ["logger"]
