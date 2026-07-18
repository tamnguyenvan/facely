"""Recognition service for face matching."""
import threading
import queue
import time
import numpy as np
from app.core.model_manager import ModelManager
from app.core.detector import FaceDetector
from app.core.matcher import EmbeddingMatcher
from app.db.identity_repo import IdentityRepository
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RecognitionService:
    """Orchestrates face detection, embedding, and matching."""
    
    def __init__(
        self,
        model_manager: ModelManager,
        detector: FaceDetector,
        matcher: EmbeddingMatcher,
        repo: IdentityRepository,
    ):
        self._mm = model_manager
        self._detector = detector
        self._matcher = matcher
        self._repo = repo
        self.result_queue: queue.Queue = queue.Queue(maxsize=4)
        self._paused = threading.Event()
        self._paused.set()
    
    def set_model(self, model_name: str) -> None:
        """Switch to a different model."""
        logger.info(f"Model switch requested: {model_name}")
        self._paused.clear()
        self._mm.load(model_name)
        self.reload_cache(model_name)
        self._paused.set()
    
    def reload_cache(self, model_name: str) -> None:
        """Reload embedding cache for the current model."""
        identities = self._repo.get_all_embeddings(model_name)
        self._matcher.load_cache(identities)
    
    def process_frame(self, frame: np.ndarray, frame_num: int) -> None:
        """Process a single frame for recognition."""
        if not self._paused.is_set():
            return
        
        t0 = time.perf_counter()
        faces = self._detector.detect(frame)
        results = []
        
        for face in faces:
            crop = self._detector.crop_face(frame, face["bbox"])
            try:
                embedding = self._mm.active_model.get_embedding(crop)
                match = self._matcher.find_best(embedding)
            except Exception as e:
                logger.error(f"Embedding/match error: {e}")
                match = {"name": "Error", "score": 0.0, "person_id": None}
            
            results.append({
                "bbox": face["bbox"],
                "name": match["name"],
                "score": match["score"],
            })
        
        latency_ms = int((time.perf_counter() - t0) * 1000)
        logger.debug(
            f"Frame #{frame_num} | faces={len(faces)} | latency={latency_ms}ms"
        )
        
        try:
            self.result_queue.put_nowait({
                "frame": frame,
                "results": results,
                "latency_ms": latency_ms,
            })
        except queue.Full:
            pass
