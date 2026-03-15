# BACKEND.md — Facely Backend Reference

> Covers: Model Adapters · Core Logic · Services · Database · Logging

---

## 1. Model Layer (`app/models/`)

### 1.1 Abstract Base Interface

All model adapters inherit from `BaseModel`:

```python
# app/models/base_model.py
from abc import ABC, abstractmethod
import numpy as np

class BaseModel(ABC):
    """
    Contract that every face embedding model adapter must satisfy.
    The UI and services only ever interact with this interface.
    """

    name: str           # 'arcface' | 'sface' | 'deepface'
    input_size: tuple   # (H, W) e.g. (112, 112)
    embedding_dim: int  # e.g. 512

    @abstractmethod
    def load(self, model_path: str) -> None:
        """Load ONNX model into memory. Called once by ModelManager."""

    @abstractmethod
    def unload(self) -> None:
        """Release ONNX session and free memory."""

    @abstractmethod
    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Args:
            face_crop: Aligned face image, shape (H, W, 3), dtype uint8, RGB

        Returns:
            L2-normalized embedding vector, shape (embedding_dim,), dtype float32
        """

    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if session is ready for inference."""
```

---

### 1.2 ArcFace Adapter

**Model source:** InsightFace `buffalo_l` — `arcface_r100.onnx`
**Input:** 112×112, normalized to [-1, 1], NCHW
**Output:** float32[512], L2-normalized

```python
# app/models/arcface_model.py
import onnxruntime as ort
import numpy as np
import cv2
from .base_model import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ArcFaceModel(BaseModel):
    name = "arcface"
    input_size = (112, 112)
    embedding_dim = 512

    def __init__(self):
        self._session: ort.InferenceSession | None = None
        self._input_name: str | None = None

    def load(self, model_path: str) -> None:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 4
        self._session = ort.InferenceSession(model_path, sess_options=opts,
                                              providers=providers)
        self._input_name = self._session.get_inputs()[0].name
        logger.info(f"ArcFace loaded from {model_path}")

    def unload(self) -> None:
        self._session = None
        logger.info("ArcFace session released")

    def is_loaded(self) -> bool:
        return self._session is not None

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        img = cv2.resize(face_crop, self.input_size)
        img = img.astype(np.float32)
        img = (img - 127.5) / 127.5                  # normalize to [-1, 1]
        img = np.transpose(img, (2, 0, 1))            # HWC → CHW
        img = np.expand_dims(img, axis=0)             # → NCHW
        outputs = self._session.run(None, {self._input_name: img})
        embedding = outputs[0][0]
        return self._l2_normalize(embedding)

    @staticmethod
    def _l2_normalize(vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-10)
```

---

### 1.3 SFace Adapter

**Model source:** OpenCV Model Zoo — `sface.onnx`
**Input:** 112×112, float32, normalized
**Output:** float32[128], L2-normalized

```python
# app/models/sface_model.py
import onnxruntime as ort
import numpy as np
import cv2
from .base_model import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SFaceModel(BaseModel):
    name = "sface"
    input_size = (112, 112)
    embedding_dim = 128

    def __init__(self):
        self._session: ort.InferenceSession | None = None

    def load(self, model_path: str) -> None:
        self._session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )
        logger.info(f"SFace loaded from {model_path}")

    def unload(self) -> None:
        self._session = None

    def is_loaded(self) -> bool:
        return self._session is not None

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        img = cv2.resize(face_crop, self.input_size).astype(np.float32)
        img = img / 255.0
        mean = np.array([0.5, 0.5, 0.5])
        std  = np.array([0.5, 0.5, 0.5])
        img  = (img - mean) / std
        img  = np.transpose(img, (2, 0, 1))
        img  = np.expand_dims(img, 0)
        out  = self._session.run(None, {"data": img})
        return self._l2_normalize(out[0][0])

    @staticmethod
    def _l2_normalize(v):
        return v / (np.linalg.norm(v) + 1e-10)
```

---

### 1.4 DeepFace Adapter

**Model source:** DeepFace library (VGG-Face2 backend)
**Strategy:** Wrap `DeepFace.represent()` for embedding extraction

```python
# app/models/deepface_model.py
import numpy as np
from deepface import DeepFace
from .base_model import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DeepFaceModel(BaseModel):
    name = "deepface"
    input_size = (224, 224)
    embedding_dim = 4096   # VGG-Face2 default

    def __init__(self):
        self._loaded = False

    def load(self, model_path: str) -> None:
        # DeepFace handles its own model loading
        DeepFace.build_model("VGG-Face")
        self._loaded = True
        logger.info("DeepFace (VGG-Face) model warmed up")

    def unload(self) -> None:
        self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        result = DeepFace.represent(
            img_path=face_crop,
            model_name="VGG-Face",
            enforce_detection=False,
            detector_backend="skip",   # we handle detection upstream
        )
        vec = np.array(result[0]["embedding"], dtype=np.float32)
        return self._l2_normalize(vec)

    @staticmethod
    def _l2_normalize(v):
        return v / (np.linalg.norm(v) + 1e-10)
```

---

## 2. Core Logic (`app/core/`)

### 2.1 ModelManager

```python
# app/core/model_manager.py
from app.models.arcface_model import ArcFaceModel
from app.models.sface_model import SFaceModel
from app.models.deepface_model import DeepFaceModel
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MODEL_REGISTRY = {
    "arcface":  ArcFaceModel,
    "sface":    SFaceModel,
    "deepface": DeepFaceModel,
}

class ModelManager:
    def __init__(self):
        self._active = None
        self._active_name: str | None = None

    @property
    def active_model(self):
        return self._active

    @property
    def active_name(self) -> str | None:
        return self._active_name

    def load(self, model_name: str) -> None:
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
        if self._active:
            self._active.unload()
            logger.info(f"Unloaded model: {self._active_name}")
            self._active = None
            self._active_name = None
```

### 2.2 Detector

```python
# app/core/detector.py
"""
Face detection using OpenCV DNN (res10_300x300_ssd_iter_140000.caffemodel)
Returns bounding boxes + 5-point landmarks for alignment.
"""
import cv2
import numpy as np
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FaceDetector:
    CONF_THRESHOLD = 0.7

    def __init__(self, model_dir: str):
        proto = f"{model_dir}/deploy.prototxt"
        model = f"{model_dir}/res10_300x300_ssd.caffemodel"
        self._net = cv2.dnn.readNet(model, proto)

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Returns list of { 'bbox': (x1,y1,x2,y2), 'confidence': float }
        """
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                     (104.0, 177.0, 123.0))
        self._net.setInput(blob)
        detections = self._net.forward()
        results = []
        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < self.CONF_THRESHOLD:
                continue
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            results.append({
                "bbox": (x1, y1, x2, y2),
                "confidence": confidence,
            })
        return results

    def crop_face(self, frame: np.ndarray, bbox: tuple,
                  padding: float = 0.1) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        pad_x = int((x2 - x1) * padding)
        pad_y = int((y2 - y1) * padding)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        crop = frame[y1:y2, x1:x2]
        return cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
```

### 2.3 Matcher

```python
# app/core/matcher.py
import numpy as np
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingMatcher:
    """
    In-memory cosine similarity matcher.
    Cache structure: { person_id: np.ndarray[dim] }
    """

    def __init__(self):
        self._cache: dict[str, tuple[str, np.ndarray]] = {}
        # { person_id: (name, embedding) }

    def load_cache(self, identities: list[dict]) -> None:
        """
        identities: [{ person_id, name, embedding: np.ndarray }]
        """
        self._cache = {
            item["person_id"]: (item["name"], item["embedding"])
            for item in identities
        }
        logger.info(f"Embedding cache loaded: {len(self._cache)} identities")

    def invalidate(self) -> None:
        self._cache.clear()
        logger.debug("Embedding cache invalidated")

    def find_best(self, query: np.ndarray) -> dict:
        """
        Returns { person_id, name, score } or { name: 'Unknown', score: float }
        """
        if not self._cache:
            return {"name": "Unknown", "score": 0.0, "person_id": None}

        best_id, best_name, best_score = None, "Unknown", -1.0

        for pid, (name, stored) in self._cache.items():
            score = float(np.dot(query, stored))   # both L2-normalized → cosine
            if score > best_score:
                best_score = score
                best_id = pid
                best_name = name

        if best_score < CONFIG.similarity_threshold:
            return {"name": "Unknown", "score": best_score, "person_id": None}

        return {"name": best_name, "score": best_score, "person_id": best_id}
```

---

## 3. Service Layer (`app/services/`)

### 3.1 CameraService

```python
# app/services/camera_service.py
import threading
import queue
import cv2
from app.utils.logger import get_logger
from app.config import CONFIG

logger = get_logger(__name__)

class CameraService:
    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)

    def start(self, camera_index: int = None) -> None:
        idx = camera_index or CONFIG.camera_index
        self._cap = cv2.VideoCapture(idx)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {idx}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG.frame_height)
        self._running.set()
        self._thread = threading.Thread(target=self._capture_loop,
                                        daemon=True, name="CaptureThread")
        self._thread.start()
        logger.info(f"Camera {idx} started")

    def stop(self) -> None:
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
        logger.info("Camera stopped")

    def _capture_loop(self) -> None:
        frame_num = 0
        while self._running.is_set():
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Frame capture failed")
                continue
            frame_num += 1
            if frame_num % CONFIG.frame_skip != 0:
                # Still push raw frame for display, just mark as skip
                try:
                    self.frame_queue.put_nowait((frame, False))
                except queue.Full:
                    pass
                continue
            try:
                self.frame_queue.put_nowait((frame, True))   # True = process
            except queue.Full:
                pass
```

### 3.2 RecognitionService

```python
# app/services/recognition_service.py
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
    def __init__(self, model_manager: ModelManager,
                 detector: FaceDetector,
                 matcher: EmbeddingMatcher,
                 repo: IdentityRepository):
        self._mm = model_manager
        self._detector = detector
        self._matcher = matcher
        self._repo = repo
        self.result_queue: queue.Queue = queue.Queue(maxsize=4)
        self._paused = threading.Event()
        self._paused.set()   # starts in running state

    def set_model(self, model_name: str) -> None:
        logger.info(f"Model switch requested: {model_name}")
        self._paused.clear()
        self._mm.load(model_name)
        self.reload_cache(model_name)
        self._paused.set()

    def reload_cache(self, model_name: str) -> None:
        identities = self._repo.get_all_embeddings(model_name)
        self._matcher.load_cache(identities)

    def process_frame(self, frame, frame_num: int) -> None:
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
        logger.debug(f"Frame #{frame_num} | faces={len(faces)} | "
                     f"latency={latency_ms}ms")
        try:
            self.result_queue.put_nowait({
                "frame": frame,
                "results": results,
                "latency_ms": latency_ms,
            })
        except queue.Full:
            pass
```

### 3.3 RegistrationService

```python
# app/services/registration_service.py
import numpy as np
import uuid
from app.core.detector import FaceDetector
from app.core.model_manager import ModelManager
from app.db.identity_repo import IdentityRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RegistrationService:
    CAPTURE_FRAMES = 5   # average over N frames for robust embedding

    def __init__(self, detector: FaceDetector,
                 model_manager: ModelManager,
                 repo: IdentityRepository):
        self._detector = detector
        self._mm = model_manager
        self._repo = repo

    def register(self, name: str, frames: list,
                 person_id: str | None = None) -> str:
        """
        frames: list of BGR np.ndarray
        Returns: assigned person_id
        """
        embeddings = []
        for frame in frames:
            faces = self._detector.detect(frame)
            if not faces:
                continue
            crop = self._detector.crop_face(frame, faces[0]["bbox"])
            emb = self._mm.active_model.get_embedding(crop)
            embeddings.append(emb)

        if not embeddings:
            raise ValueError("No faces detected in capture frames")

        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

        pid = person_id or str(uuid.uuid4())[:8].upper()
        self._repo.upsert_identity(
            name=name,
            person_id=pid,
            model_name=self._mm.active_name,
            embedding=avg_embedding,
        )
        logger.info(f"Registered: {name} ({pid}) via {self._mm.active_name}")
        return pid
```

---

## 4. Database Layer (`app/db/`)

### 4.1 Connection & Migrations

```python
# app/db/database.py
import sqlite3
from pathlib import Path
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)

class Database:
    def __init__(self, db_path: Path = None):
        self._path = db_path or CONFIG.db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self) -> None:
        schema = Path(__file__).parent / "schema.sql"
        conn = self.get_connection()
        with conn:
            conn.executescript(schema.read_text())
        logger.info(f"Database initialized at {self._path}")

    def integrity_check(self) -> bool:
        conn = self.get_connection()
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result[0] == "ok"
```

### 4.2 Identity Repository

```python
# app/db/identity_repo.py
import numpy as np
from app.db.database import Database
from app.utils.logger import get_logger

logger = get_logger(__name__)

class IdentityRepository:
    def __init__(self, db: Database):
        self._db = db

    def upsert_identity(self, name: str, person_id: str,
                        model_name: str, embedding: np.ndarray) -> None:
        conn = self._db.get_connection()
        with conn:
            conn.execute("""
                INSERT INTO identities (name, person_id)
                VALUES (?, ?)
                ON CONFLICT(person_id) DO UPDATE SET
                    name = excluded.name,
                    updated_at = datetime('now')
            """, (name, person_id))

            row = conn.execute(
                "SELECT id FROM identities WHERE person_id = ?", (person_id,)
            ).fetchone()

            conn.execute("""
                INSERT INTO embeddings (identity_id, model_name, vector)
                VALUES (?, ?, ?)
                ON CONFLICT DO NOTHING
            """, (row["id"], model_name, embedding.tobytes()))

    def get_all_embeddings(self, model_name: str) -> list[dict]:
        conn = self._db.get_connection()
        rows = conn.execute("""
            SELECT i.person_id, i.name, e.vector
            FROM embeddings e
            JOIN identities i ON i.id = e.identity_id
            WHERE e.model_name = ?
        """, (model_name,)).fetchall()

        result = []
        for row in rows:
            vec = np.frombuffer(row["vector"], dtype=np.float32).copy()
            result.append({
                "person_id": row["person_id"],
                "name": row["name"],
                "embedding": vec,
            })
        return result

    def delete_identity(self, person_id: str) -> None:
        conn = self._db.get_connection()
        with conn:
            conn.execute("DELETE FROM identities WHERE person_id = ?",
                         (person_id,))
        logger.info(f"Deleted identity: {person_id}")

    def list_identities(self) -> list[dict]:
        conn = self._db.get_connection()
        rows = conn.execute(
            "SELECT person_id, name, created_at FROM identities ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
```

---

## 5. Logging (`app/utils/logger.py`)

Facely uses Python's standard `logging` module with three handlers:

### 5.1 Logger Setup

```python
# app/utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import CONFIG

_initialized = False

def _setup_logging() -> None:
    global _initialized
    if _initialized:
        return

    log_dir = CONFIG.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(getattr(logging, CONFIG.log_level))

    # ── Console handler (color-friendly)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    # ── Main rotating file handler (all levels)
    main_handler = RotatingFileHandler(
        filename=log_dir / "Facely.log",
        maxBytes=CONFIG.max_log_size_mb * 1024 * 1024,
        backupCount=CONFIG.log_backup_count,
        encoding="utf-8",
    )
    main_handler.setLevel(logging.DEBUG)
    main_handler.setFormatter(fmt)
    root.addHandler(main_handler)

    # ── Error-only file handler
    error_handler = RotatingFileHandler(
        filename=log_dir / "Facely_error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)
    root.addHandler(error_handler)

    # ── Performance logger (separate)
    perf_logger = logging.getLogger("Facely.perf")
    perf_handler = RotatingFileHandler(
        filename=log_dir / "Facely_perf.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    perf_handler.setFormatter(fmt)
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    _setup_logging()
    return logging.getLogger(name)
```

### 5.2 Logging Conventions

| Level | When to use |
|---|---|
| `DEBUG` | Per-frame metrics, embedding details, cache lookups |
| `INFO` | Model load/unload, registration, camera start/stop |
| `WARNING` | Frame drops, low-confidence matches, degraded performance |
| `ERROR` | Embedding failures, DB errors, thread exceptions |
| `CRITICAL` | Unrecoverable errors, app startup failures |

### 5.3 Sample Log Output

```
2024-01-15 14:23:01.442 | INFO     | app.services.recognition_service | Active model → arcface
2024-01-15 14:23:01.891 | INFO     | app.services.camera_service      | Camera 0 started
2024-01-15 14:23:02.104 | DEBUG    | app.core.matcher                 | Embedding cache loaded: 12 identities
2024-01-15 14:23:03.441 | DEBUG    | app.services.recognition_service | Frame #6 | faces=1 | latency=22ms
2024-01-15 14:23:03.441 | WARNING  | app.core.matcher                 | Low confidence: 0.41 → Unknown
2024-01-15 14:23:10.001 | INFO     | app.services.registration_service| Registered: Alice (A1F3B2) via arcface
```

---

## 6. Model Download Reference

| Model | File | Source | Size |
|---|---|---|---|
| ArcFace | `arcface_r100.onnx` | InsightFace / buffalo_l | ~249 MB |
| SFace | `sface.onnx` | OpenCV Model Zoo | ~37 MB |
| DeepFace VGG-Face2 | via `deepface` library | Auto-downloaded | ~550 MB |
| Detection | `res10_300x300_ssd.caffemodel` | OpenCV DNN | ~10 MB |

> **Note:** ArcFace and SFace must be placed in `assets/models/`. DeepFace downloads its weights to `~/.deepface/` on first run.