from loguru import logger
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Clear any existing handlers (default is stdout)
logger.remove()

# === CONFIGURATION ===
# File filtering options:
# - Set to None to disable filtering (show all logs)
# - Set to a list of filenames to show only those files

FILTER_FILES = None  # e.g., ["quic_server.py", "client_manager.py"]

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

# === FILTER FUNCTION ===
def file_filter(record):
    """Filter logs by file name based on FILTER_FILES configuration"""
    if FILTER_FILES is None:
        return True  # No filtering
    return record["file"].name in FILTER_FILES

# === HANDLERS ===

# Terminal logging (for dev/debug)
logger.add(
    sys.stdout,
    level="DEBUG",
    format=STDOUT_FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=True,
    filter=file_filter
)

# Debug log file
logger.add(
    "logs/debug.log",
    level="DEBUG",
    format=FILE_FORMAT,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    filter=file_filter
)

# Info log file (only INFO)
logger.add(
    "logs/info.log",
    level="INFO",
    format=FILE_FORMAT,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,
    filter=lambda record: file_filter(record) and record["level"].name == "INFO"
)

# Warning log file (WARNING and above, but not ERROR/CRITICAL)
logger.add(
    "logs/warning.log",
    level="WARNING",
    format=FILE_FORMAT,
    rotation="5 MB",
    retention="15 days",
    compression="zip",
    enqueue=True,
    filter=lambda record: file_filter(record) and record["level"].name == "WARNING"
)

# Error log file (ERROR and above)
logger.add(
    "logs/error.log",
    level="ERROR",
    format=FILE_FORMAT,
    rotation="5 MB",
    retention="15 days",
    compression="zip",
    enqueue=True,
    filter=file_filter
)

# Expose logger for import
__all__ = ["logger"]
