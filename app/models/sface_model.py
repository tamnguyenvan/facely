"""SFace model adapter using OpenCV FaceRecognizerSF."""
import cv2 as cv
import numpy as np
from numpy.typing import NDArray
from typing import Any, Union, List, cast

from .base_model import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SFaceModel(BaseModel):
    """SFace model adapter (OpenCV Model Zoo)."""

    name = "sface"
    input_size = (112, 112)
    embedding_dim = 128

    def __init__(self):
        self._model: cv.FaceRecognizerSF | None = None

    def load(self, model_path: str) -> None:
        """Load SFace ONNX model using OpenCV FaceRecognizerSF."""
        try:
            self._model = cv.FaceRecognizerSF.create(
                model=model_path, config="", backend_id=0, target_id=0
            )
        except Exception as err:
            raise ValueError(
                "Exception while calling opencv.FaceRecognizerSF module. "
                "This is an optional dependency. "
                "You can install it as pip install opencv-contrib-python."
            ) from err

        logger.info(f"SFace loaded from {model_path}")

    def unload(self) -> None:
        """Release SFace model."""
        self._model = None
        logger.info("SFace model released")

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def get_embedding(self, face_crop: NDArray[np.floating]) -> NDArray[np.floating]:
        """Extract SFace embedding from face crop.

        Args:
            face_crop: Pre-loaded face image in BGR format

        Returns:
            128-dimensional embedding vector
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")

        # SFace expects BGR uint8 input
        input_blob = (face_crop * 255).astype(np.uint8)

        # Extract features
        embedding = self._model.feature(input_blob)

        return self._l2_normalize(embedding[0])

    def forward(
        self, img: NDArray[Any]
    ) -> Union[List[float], List[List[float]]]:
        """Find embeddings with SFace model.

        Args:
            img: Pre-loaded image in BGR format

        Returns:
            Embeddings as list of floats or list of lists
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")

        input_blob = (img * 255).astype(np.uint8)
        embeddings = []

        for i in range(input_blob.shape[0]):
            embedding = self._model.feature(input_blob[i])
            embeddings.append(embedding)

        embeddings_np = np.concatenate(embeddings, axis=0)

        if embeddings_np.shape[0] == 1:
            return cast(List[float], embeddings_np[0].tolist())
        return cast(List[List[float]], embeddings_np.tolist())

    @staticmethod
    def _l2_normalize(v: NDArray[np.floating]) -> NDArray[np.floating]:
        """L2 normalize vector."""
        norm = np.linalg.norm(v)
        if norm > 0:
            return v / norm
        return v