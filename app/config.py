"""Central configuration for Facely."""
import sys
from dataclasses import dataclass
from pathlib import Path


def _base_path() -> Path:
    """Get base path for assets (handles PyInstaller frozen mode)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with all tuneable parameters."""
    
    # Camera
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    frame_skip: int = 2
    
    # Recognition
    similarity_threshold: float = 0.55
    embedding_dim: int = 512
    default_model: str = "arcface"
    
    # Paths
    base_path: Path = _base_path()
    db_path: Path = base_path / "data" / "Facely.db"
    log_dir: Path = base_path / "logs"
    model_dir: Path = base_path / "assets" / "models"
    
    # Logging
    log_level: str = "INFO"
    max_log_size_mb: int = 10
    log_backup_count: int = 5


CONFIG = AppConfig()
