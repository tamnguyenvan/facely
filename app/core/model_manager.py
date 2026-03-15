"""Model manager for loading and switching face recognition models."""
from app.models.arcface_model import ArcFaceModel
from app.models.deepface_model import DeepFaceModel
from app.models.sface_model import SFaceModel
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MODEL_REGISTRY = {
    "arcface": ArcFaceModel,
    "deepface": DeepFaceModel,
    "sface": SFaceModel,
}


class ModelManager:
    """Manages loading and switching of face recognition models."""
    
    def __init__(self):
        self._active = None
        self._active_name: str | None = None
    
    @property
    def active_model(self):
        """Get the currently active model."""
        return self._active
    
    @property
    def active_name(self) -> str | None:
        """Get the name of the currently active model."""
        return self._active_name
    
    def load(self, model_name: str) -> None:
        """Load a model by name."""
        if model_name not in _MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_name}")
        
        if self._active and self._active.is_loaded():
            self.unload_current()
        
        model_path = str(CONFIG.model_dir / f"{model_name}.onnx")
        instance = _MODEL_REGISTRY[model_name]()
        instance.load(model_path)
        self._active = instance
        self._active_name = model_name
        logger.info(f"Active model → {model_name}")
    
    def unload_current(self) -> None:
        """Unload the currently active model."""
        if self._active:
            self._active.unload()
            logger.info(f"Unloaded model: {self._active_name}")
            self._active = None
            self._active_name = None
