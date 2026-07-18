"""Camera service for video capture."""
import threading
import queue
import cv2
from app.utils.logger import get_logger
from app.config import CONFIG

logger = get_logger(__name__)


class CameraService:
    """Manages camera capture in a background thread."""
    
    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
    
    def start(self, camera_index: int | None = None) -> None:
        """Start camera capture."""
        idx = camera_index if camera_index is not None else CONFIG.camera_index
        self._cap = cv2.VideoCapture(idx)
        
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {idx}")
        
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG.frame_height)
        
        self._running.set()
        self._thread = threading.Thread(
            target=self._capture_loop, daemon=True, name="CaptureThread"
        )
        self._thread.start()
        logger.info(f"Camera {idx} started")
    
    def stop(self) -> None:
        """Stop camera capture."""
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
        logger.info("Camera stopped")
    
    def _capture_loop(self) -> None:
        """Background capture loop."""
        frame_num = 0
        while self._running.is_set():
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Frame capture failed")
                continue
            
            frame_num += 1
            should_process = (frame_num % CONFIG.frame_skip == 0)
            
            try:
                self.frame_queue.put_nowait((frame, should_process))
            except queue.Full:
                pass
