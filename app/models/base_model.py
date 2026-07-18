"""Abstract base interface for face recognition models."""
from abc import ABC, abstractmethod
import numpy as np


class BaseModel(ABC):
    """Contract that every face embedding model adapter must satisfy."""
    
    name: str
    input_size: tuple[int, int]
    embedding_dim: int
    
    @abstractmethod
    def load(self, model_path: str) -> None:
        """Load model into memory."""
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Release model and free memory."""
        pass
    
    @abstractmethod
    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Extract embedding from aligned face crop.
        
        Args:
            face_crop: Aligned face image, shape (H, W, 3), dtype uint8, RGB
        
        Returns:
            L2-normalized embedding vector, shape (embedding_dim,), dtype float32
        """
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if model is ready for inference."""
        pass
