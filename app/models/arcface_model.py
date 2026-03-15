"""ArcFace model adapter using ONNX Runtime."""
import onnxruntime as ort
import numpy as np
import cv2
from .base_model import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ArcFaceModel(BaseModel):
    """ArcFace model adapter (InsightFace buffalo_l)."""
    
    name = "arcface"
    input_size = (112, 112)
    embedding_dim = 512
    
    def __init__(self):
        self._session: ort.InferenceSession | None = None
        self._input_name: str | None = None
        self._format: str = "NCHW"  # Default format
    
    def load(self, model_path: str) -> None:
        """Load ArcFace ONNX model."""
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 4
        
        self._session = ort.InferenceSession(
            model_path, sess_options=opts, providers=providers
        )
        self._input_name = self._session.get_inputs()[0].name
        
        # Check input shape to determine format (NCHW vs NHWC)
        input_shape = self._session.get_inputs()[0].shape
        logger.info(f"ArcFace model input shape: {input_shape}")
        
        # Determine if model expects NCHW or NHWC
        # NCHW: (batch, channels, height, width) - e.g., (1, 3, 112, 112)
        # NHWC: (batch, height, width, channels) - e.g., (1, 112, 112, 3)
        if len(input_shape) == 4:
            if input_shape[1] == 3 or input_shape[1] == 1:
                self._format = "NCHW"
            elif input_shape[3] == 3 or input_shape[3] == 1:
                self._format = "NHWC"
            else:
                # Default to NCHW
                self._format = "NCHW"
        else:
            self._format = "NCHW"
        
        logger.info(f"ArcFace loaded from {model_path} (format: {self._format})")
    
    def unload(self) -> None:
        """Release ArcFace session."""
        self._session = None
        logger.info("ArcFace session released")
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._session is not None
    
    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """Extract ArcFace embedding."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")
        
        # Preprocess - face_crop is already RGB from detector
        img = cv2.resize(face_crop, self.input_size)
        img = img.astype(np.float32)
        img = (img - 127.5) / 127.5  # Normalize to [-1, 1]
        
        # Format based on model requirements
        if self._format == "NCHW":
            img = np.transpose(img, (2, 0, 1))  # HWC → CHW
            img = np.expand_dims(img, axis=0)  # → NCHW (1, 3, 112, 112)
        else:  # NHWC
            img = np.expand_dims(img, axis=0)  # → NHWC (1, 112, 112, 3)
        
        # Inference
        outputs = self._session.run(None, {self._input_name: img})
        embedding = outputs[0][0]
        
        return self._l2_normalize(embedding)
    
    @staticmethod
    def _l2_normalize(vec: np.ndarray) -> np.ndarray:
        """L2 normalize vector."""
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-10)
