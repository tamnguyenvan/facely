#!/usr/bin/env python3
"""Initialize the Facely database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import Database
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Initialize database."""
    print("Initializing Facely database...")
    db = Database()
    
    try:
        db.initialize()
        print("✓ Database initialized successfully")
        print(f"  Location: {db._path}")
        
        if db.integrity_check():
            print("✓ Database integrity check passed")
        else:
            print("✗ Database integrity check failed")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
