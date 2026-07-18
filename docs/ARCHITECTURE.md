# ARCHITECTURE.md — Facely System Design

> Production-grade architecture for a modular, offline facial recognition desktop application.

---

## 1. Design Philosophy

Facely is designed around four principles:

| Principle | Application |
|---|---|
| **Separation of Concerns** | UI never touches models directly; service layer mediates everything |
| **Replaceability** | Any model can be swapped without touching UI or DB code |
| **Offline-first** | Zero network dependency at runtime |
| **Observable** | Every layer emits structured logs; failures are traceable |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER (Tkinter UI)              │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │
│  │ CameraPanel  │  │  ControlPanel    │  │    IdentityPanel      │ │
│  │ (Live Feed)  │  │ (Model/Start/Stop│  │ (Register / List)     │ │
│  └──────┬───────┘  └────────┬─────────┘  └──────────┬────────────┘ │
└─────────┼───────────────────┼────────────────────────┼─────────────┘
          │ frames            │ commands               │ identity ops
          ▼                   ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SERVICE LAYER                                 │
│  ┌───────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  CameraService    │  │ RecognitionService│  │RegistrationSvc   │ │
│  │  (thread + queue) │  │ (orchestrates     │  │(capture+embed    │ │
│  │                   │  │  detect+embed     │  │ +store)          │ │
│  │                   │  │  +match)          │  │                  │ │
│  └───────────────────┘  └────────┬─────────┘  └────────┬─────────┘ │
└────────────────────────────────┬─┘────────────────────┬─────────────┘
                                 │                       │
          ┌──────────────────────┼───────────────────────┤
          ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CORE / MODEL LAYER                          │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐   │
│  │   Detector   │   │  ModelManager│   │       Matcher         │   │
│  │ (face crop & │   │  (ONNX load/ │   │ (cosine sim, thresh,  │   │
│  │  align)      │   │   hot-swap)  │   │  top-k search)        │   │
│  └──────────────┘   └──────┬───────┘   └───────────────────────┘   │
│                             │                                        │
│              ┌──────────────┼─────────────────┐                     │
│              ▼              ▼                 ▼                      │
│        ┌──────────┐  ┌──────────┐  ┌──────────────┐                │
│        │ ArcFace  │  │  SFace   │  │  DeepFace    │                │
│        │ Adapter  │  │ Adapter  │  │  Adapter     │                │
│        └──────────┘  └──────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA ACCESS LAYER                             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  IdentityRepository  (SQLite via sqlite3)                     │  │
│  │  • upsert_identity()   • get_all_embeddings()                 │  │
│  │  • delete_identity()   • search_by_name()                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  SQLite DB  →  Facely.db                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer Responsibilities

### 3.1 Presentation Layer (`app/ui/`)

- Renders camera frames via Tkinter `Canvas` (PhotoImage swap)
- Subscribes to service callbacks via Python callables (no direct polling)
- Does **not** import from `app/models/` or `app/db/` directly
- All UI mutations happen on the **main thread** (enforced via `root.after()`)

### 3.2 Service Layer (`app/services/`)

Thin orchestration objects that wire core components together.

| Service | Responsibility |
|---|---|
| `CameraService` | Opens `cv2.VideoCapture`, runs capture loop in daemon thread, pushes frames to a `queue.Queue` |
| `RecognitionService` | Pulls frames from queue → detect faces → extract embeddings → match → emit results |
| `RegistrationService` | Captures N frames → averages embeddings → writes to DB |

### 3.3 Core / Model Layer (`app/core/`, `app/models/`)

Pure algorithmic code with zero UI or DB dependencies.

| Component | Responsibility |
|---|---|
| `Detector` | OpenCV DNN or ONNX-based face detection + landmark alignment |
| `ModelManager` | Loads/unloads ONNX sessions; enforces single active model |
| `Embedder` | Delegates to active model adapter; returns `np.ndarray` |
| `Matcher` | Cosine similarity search over in-memory embedding cache |

### 3.4 Data Access Layer (`app/db/`)

- SQLite connection with WAL mode enabled
- `IdentityRepository` exposes typed methods only; raw SQL stays inside
- Embeddings stored as `BLOB` (NumPy `tobytes()` / `frombuffer()`)

---

## 4. Threading Model

```
Main Thread (Tkinter event loop)
    │
    ├── CameraService.daemon_thread
    │       └── cv2.VideoCapture.read()
    │           └── frame_queue.put(frame)
    │
    ├── RecognitionWorker.daemon_thread
    │       └── frame_queue.get()
    │           ├── Detector.detect()
    │           ├── Embedder.extract()
    │           ├── Matcher.find_best()
    │           └── result_queue.put(result)
    │
    └── UI Poller  (root.after(30, poll_results))
            └── result_queue.get_nowait()
                └── CameraPanel.update_overlay()
```

**Rules:**
- Only the main thread calls any `tkinter` API
- `frame_queue` and `result_queue` are `queue.Queue` (thread-safe)
- Workers are daemon threads (auto-killed on app exit)
- Frame skip (`FRAME_SKIP=2`) reduces CPU load without UI stutter

---

## 5. Model Hot-Swap Protocol

```
User clicks model selector
    → ControlPanel emits on_model_change(model_name)
    → RecognitionService.set_model(model_name)
        → RecognitionWorker pauses (threading.Event.clear())
        → ModelManager.unload_current()
        → ModelManager.load(model_name)      # ONNX session init
        → EmbeddingCache.invalidate()        # force re-embed
        → RecognitionWorker.resume()
```

The UI is non-blocking during the swap; a loading indicator is shown via `ControlPanel`.

---

## 6. Face Recognition Pipeline (per-frame)

```
Raw Frame (BGR, 1280×720)
    │
    ▼ Detector.detect()
Detected Faces [ {bbox, landmarks} ]
    │
    ▼ image_utils.align_face()
Aligned Face Crops (112×112, RGB normalized)
    │
    ▼ Embedder.extract(crop)
Embedding Vectors  [ float32[512] ]
    │
    ▼ Matcher.find_best(embedding)
    ├── Load embedding cache (in-memory numpy array)
    ├── Compute cosine similarity  (dot / (||a|| * ||b||))
    ├── Find argmax
    └── Apply threshold (SIMILARITY_THRESHOLD = 0.55)
        ├── score >= threshold → { name, id, score }
        └── score <  threshold → { name: "Unknown", score }
    │
    ▼ Result emitted to UI
Overlay rendered on Canvas (bbox + label + confidence bar)
```

---

## 7. Database Schema

```sql
-- schema.sql

CREATE TABLE IF NOT EXISTS identities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    person_id   TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS embeddings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_id  INTEGER NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    model_name   TEXT    NOT NULL,           -- 'arcface' | 'sface' | 'deepface'
    vector       BLOB    NOT NULL,           -- float32 numpy array bytes
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_embeddings_identity ON embeddings(identity_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model    ON embeddings(model_name);
```

> Embeddings are stored **per model** — switching models does not invalidate other models' stored embeddings.

---

## 8. Embedding Cache Strategy

At startup and after every registration:

```python
# In RecognitionService.__init__ and after registration
cache = {
    "arcface":  { person_id: np.ndarray[512] },
    "sface":    { person_id: np.ndarray[512] },
    "deepface": { person_id: np.ndarray[512] },
}
```

- Cache lives in RAM (no disk I/O during recognition loop)
- Rebuilt on startup from DB, and after any registration/deletion
- `Matcher` operates entirely on this cache

---

## 9. Configuration Management

`app/config.py` is the **single source of truth** for all tuneable values.

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class AppConfig:
    # Camera
    camera_index: int       = 0
    frame_width: int        = 1280
    frame_height: int       = 720
    frame_skip: int         = 2

    # Recognition
    similarity_threshold: float = 0.55
    embedding_dim: int          = 512
    default_model: str          = "arcface"

    # Paths
    db_path: Path   = Path("data/Facely.db")
    log_dir: Path   = Path("logs")
    model_dir: Path = Path("assets/models")

    # Logging
    log_level: str         = "INFO"
    max_log_size_mb: int   = 10
    log_backup_count: int  = 5

CONFIG = AppConfig()
```

Environment overrides can be applied via a `.env` file using `python-dotenv` (optional).

---

## 10. Error Handling Strategy

| Failure | Handling |
|---|---|
| Camera not found | `CameraService` raises `CameraError`; UI shows modal dialog |
| Model file missing | `ModelManager` raises `ModelLoadError`; fallback to last good model |
| DB corruption | `Database.__init__` re-creates schema if integrity check fails |
| Embedding mismatch (dim) | Logged as WARNING; embedding silently discarded |
| Thread crash | Worker threads wrap loops in `try/except`; log CRITICAL + notify UI |

---

## 11. Logging Architecture

See `BACKEND.md § Logging` for full implementation. Summary:

```
logs/
├── Facely.log          # Rotating: 10 MB × 5 backups
├── Facely_error.log    # ERROR+ only (separate handler)
└── Facely_perf.log     # FPS, inference time, match latency
```

Log format (structured):
```
2024-01-15 14:23:01.442 | INFO     | recognition_service | Frame #1024 | model=arcface | faces=2 | match=Alice(0.87) | latency=18ms
```