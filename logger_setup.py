# logger_setup.py
# Central logging configuration for the entire project.
# Every other module imports get_logger() from here.

import logging
import logging.handlers   # for RotatingFileHandler
import os


# ── Constants ────────────────────────────────────────────────
LOG_DIR          = "logs"
PERFORMANCE_LOG  = os.path.join(LOG_DIR, "performance.log")
ERROR_LOG        = os.path.join(LOG_DIR, "errors.log")

# Max size per log file before it rotates (5 MB)
MAX_BYTES        = 5 * 1024 * 1024

# How many backup files to keep (e.g. performance.log.1, .2, .3)
BACKUP_COUNT     = 3

# Log line format:
# 2024-01-15 14:23:01 | INFO     | module_name | your message here
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """
    Configure the root logger once at application startup.

    Creates:
      - performance.log  : INFO and above (all normal activity)
      - errors.log       : WARNING and above (problems only)
      - Console output   : INFO and above (live terminal view)

    Call this ONCE at the top of your main entry point.
    """

    # Make sure the logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create formatter — applied to every log message
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── Handler 1: performance.log ────────────────────────────
    # Captures INFO, WARNING, ERROR, CRITICAL
    # Rotates when file hits 5 MB, keeps 3 backups
    perf_handler = logging.handlers.RotatingFileHandler(
        filename     = PERFORMANCE_LOG,
        maxBytes     = MAX_BYTES,
        backupCount  = BACKUP_COUNT,
        encoding     = "utf-8"
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(formatter)

    # ── Handler 2: errors.log ─────────────────────────────────
    # Captures WARNING, ERROR, CRITICAL only
    # Keeps only serious problems — easier to scan
    error_handler = logging.handlers.RotatingFileHandler(
        filename     = ERROR_LOG,
        maxBytes     = MAX_BYTES,
        backupCount  = BACKUP_COUNT,
        encoding     = "utf-8"
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)

    # ── Handler 3: Console (terminal) ─────────────────────────
    # Shows live output while you're running the program
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ── Root logger ───────────────────────────────────────────
    # All loggers in the project inherit from this
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)   # capture everything at root level
                                           # handlers filter by their own level

    # Avoid adding duplicate handlers if setup_logging() is called twice
    if not root_logger.handlers:
        root_logger.addHandler(perf_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a specific module.

    Usage in any file:
        from logger_setup import get_logger
        logger = get_logger(__name__)
        logger.info("Monitoring started")

    Args:
        name : Use __name__ so the logger shows the module name

    Returns:
        A configured Logger instance
    """
    return logging.getLogger(name)
