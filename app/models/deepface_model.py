"""DeepFace model adapter using ONNX Runtime."""
import onnxruntime as ort
import numpy as np
import cv2
from .base_model import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DeepFaceModel(BaseModel):
    """DeepFace model adapter (VGG-Face based)."""

    name = "deepface"
    input_size = (152, 152)
    embedding_dim = 4096

    def __init__(self):
        self._session: ort.InferenceSession | None = None
        self._input_name: str | None = None
        self._output_name: str | None = None

    def load(self, model_path: str) -> None:
        """Load DeepFace ONNX model."""
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 4

        self._session = ort.InferenceSession(
            model_path, sess_options=opts, providers=providers
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name

        input_shape = self._session.get_inputs()[0].shape
        logger.info(f"DeepFace model input shape: {input_shape}")
        logger.info(f"DeepFace loaded from {model_path}")

    def unload(self) -> None:
        """Release DeepFace session."""
        self._session = None
        logger.info("DeepFace session released")

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._session is not None

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """Extract DeepFace embedding."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")

        # Preprocess - face_crop is already RGB from detector
        img = cv2.resize(face_crop, self.input_size)
        img = img.astype(np.float32)

        # DeepFace/VGG-Face normalization (ImageNet-based)
        img = img / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img = (img - mean) / std

        # HWC → CHW
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        # Inference
        outputs = self._session.run(None, {self._input_name: img})
        embedding = outputs[0][0]

        return self._l2_normalize(embedding)

    @staticmethod
    def _l2_normalize(vec: np.ndarray) -> np.ndarray:
        """L2 normalize vector."""
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-10)