import os
import sys
import datetime
from loguru import logger
from pathlib import Path

# Create a session-specific log directory with timestamp
# If SESSION_TIMESTAMP env var is set (e.g. from central-server subprocess), use it to keep logs in one folder
SESSION_TIMESTAMP = os.environ.get("SESSION_TIMESTAMP") or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_DIR = Path("logs") / SESSION_TIMESTAMP

# Create logs directory if it doesn't exist
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Clear any existing handlers (default is stdout)
logger.remove()

# === FORMATTERS ===

# Standard formatter for development logs
STDOUT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# File log format: more detailed and structured for debugging
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} - {message}"
)

# === HANDLERS ===

# Terminal logging (for dev/debug)
logger.add(
    sys.stdout,
    level="DEBUG",
    format=STDOUT_FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=True  # Display variables in tracebacks
)

# Debug log file
logger.add(
    LOG_DIR / "debug.log",
    level="DEBUG",
    format=FILE_FORMAT,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,  # Better performance in multi-threaded apps
    backtrace=True,
    diagnose=True
)

# Info log file (only INFO)
logger.add(
    LOG_DIR / "info.log",
    level="INFO",
    format=FILE_FORMAT,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,
    filter=lambda record: record["level"].name == "INFO"
)

# Warning log file (WARNING and above, but not ERROR/CRITICAL)
logger.add(
    LOG_DIR / "warning.log",
    level="WARNING",
    format=FILE_FORMAT,
    rotation="5 MB",
    retention="15 days",
    compression="zip",
    enqueue=True,
    filter=lambda record: record["level"].name == "WARNING"
)

# Error log file (ERROR and above)
logger.add(
    LOG_DIR / "error.log",
    level="ERROR",
    format=FILE_FORMAT,
    rotation="5 MB",
    retention="15 days",
    compression="zip",
    enqueue=True
)

# Expose logger + session log dir for import
__all__ = ["logger", "SESSION_TIMESTAMP", "LOG_DIR"]
