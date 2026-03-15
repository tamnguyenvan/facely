"""Logging configuration for Facely."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import CONFIG

_initialized = False


def _setup_logging() -> None:
    """Initialize logging handlers and formatters."""
    global _initialized
    if _initialized:
        return

    log_dir = CONFIG.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(getattr(logging, CONFIG.log_level))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    # Main rotating file handler
    main_handler = RotatingFileHandler(
        filename=log_dir / "Facely.log",
        maxBytes=CONFIG.max_log_size_mb * 1024 * 1024,
        backupCount=CONFIG.log_backup_count,
        encoding="utf-8",
    )
    main_handler.setLevel(logging.DEBUG)
    main_handler.setFormatter(fmt)
    root.addHandler(main_handler)

    # Error-only file handler
    error_handler = RotatingFileHandler(
        filename=log_dir / "Facely_error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)
    root.addHandler(error_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    _setup_logging()
    return logging.getLogger(name)
