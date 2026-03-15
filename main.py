#!/usr/bin/env python3
"""
Facely — Facial Recognition Desktop System
Entry point for the application.
"""
import sys
from pathlib import Path

# Ensure app module is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.ui.app_window import run_app
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Initialize and run the Facely application."""
    try:
        logger.info("Starting Facely...")
        run_app()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
