"""Database connection and initialization."""
import sqlite3
from pathlib import Path
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: Path | None = None):
        self._path = db_path or CONFIG.db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper settings."""
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def initialize(self) -> None:
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        conn = self.get_connection()
        try:
            with conn:
                conn.executescript(schema_path.read_text())
            logger.info(f"Database initialized at {self._path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            conn.close()
    
    def integrity_check(self) -> bool:
        """Check database integrity."""
        conn = self.get_connection()
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            return result[0] == "ok"
        finally:
            conn.close()
