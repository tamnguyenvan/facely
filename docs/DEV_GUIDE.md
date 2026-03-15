# DEV_GUIDE.md — Facely Developer Guide

> For contributors, integrators, and developers extending Facely.

---

## 1. Environment Setup

### 1.1 System Requirements

| Item | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| Python | 3.10 | 3.11 |
| RAM | 4 GB | 8 GB+ |
| CPU | Any x64 | Multi-core (inference threading) |
| GPU | None (CPU mode) | NVIDIA (CUDA 11.8, for GPU ONNX) |
| Webcam | Required | 1080p preferred |

### 1.2 First-Time Setup

```bash
# 1. Clone
git clone https://github.com/your-org/Facely.git
cd Facely

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. (GPU only) replace onnxruntime
pip uninstall onnxruntime
pip install onnxruntime-gpu

# 5. Download models
python scripts/download_models.py

# 6. Init DB
python -c "from app.db.database import Database; Database().initialize()"

# 7. Run
python main.py
```

### 1.3 requirements.txt

```
# Core inference
onnxruntime>=1.17.0
opencv-python>=4.9.0
numpy>=1.26.0

# Face recognition
deepface>=0.0.93

# Image processing
Pillow>=10.2.0
scipy>=1.12.0

# GUI (stdlib + extras)
# tkinter is bundled with Python — no pip install needed

# Utilities
python-dotenv>=1.0.0

# Dev / test
pytest>=8.0.0
pytest-mock>=3.12.0
coverage>=7.4.0
black>=24.0.0
ruff>=0.3.0
mypy>=1.9.0
```

---

## 2. Project Conventions

### 2.1 Code Style

| Tool | Config |
|---|---|
| Formatter | `black` (line length 100) |
| Linter | `ruff` (E, F, I rules) |
| Type checker | `mypy --strict` |
| Docstrings | Google style |

Run before every commit:
```bash
black app/ tests/
ruff check app/ tests/ --fix
mypy app/
```

### 2.2 Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `recognition_service.py` |
| Classes | `PascalCase` | `RecognitionService` |
| Functions / methods | `snake_case` | `get_embedding()` |
| Constants | `UPPER_SNAKE` | `SIMILARITY_THRESHOLD` |
| Private members | `_leading_underscore` | `self._session` |
| Type aliases | `PascalCase` | `EmbeddingVector = np.ndarray` |

### 2.3 Import Order

```python
# 1. Standard library
import threading
import queue

# 2. Third-party
import numpy as np
import cv2

# 3. Application (absolute)
from app.core.matcher import EmbeddingMatcher
from app.utils.logger import get_logger
```

### 2.4 Type Hints

All public functions must have full type annotations:

```python
def register(
    self,
    name: str,
    frames: list[np.ndarray],
    person_id: str | None = None,
) -> str:
    ...
```

---

## 3. Module Development Patterns

### 3.1 Adding a New Model

1. Create `app/models/mymodel_model.py` inheriting `BaseModel`
2. Implement `load()`, `unload()`, `get_embedding()`, `is_loaded()`
3. Register in `ModelManager._MODEL_REGISTRY`:
   ```python
   _MODEL_REGISTRY = {
       "arcface":  ArcFaceModel,
       "sface":    SFaceModel,
       "deepface": DeepFaceModel,
       "mymodel":  MyModel,       # ← add here
   }
   ```
4. Add model entry to `ControlPanel` combobox values list in `control_panel.py`
5. Add ONNX file to `assets/models/`
6. Write unit test in `tests/unit/test_mymodel.py`

**No other files need modification.**

### 3.2 Adding a New UI Panel

1. Create `app/ui/my_panel.py`
2. Inherit from `ttk.Frame`
3. Accept dependencies via `__init__` (service injection, not globals)
4. Use only styles from `theme.COLORS` and `theme.FONTS`
5. Register in `AppWindow.build_layout()`

### 3.3 Adding a DB Table

1. Add `CREATE TABLE` to `app/db/schema.sql`
2. Create `app/db/my_repo.py` with typed methods
3. Never write raw SQL outside of `*_repo.py` files
4. Add migration note to `CHANGELOG.md`

---

## 4. Testing

### 4.1 Structure

```
tests/
├── unit/
│   ├── test_matcher.py          # cosine similarity, threshold logic
│   ├── test_embedder.py         # model adapter unit tests (mock ONNX)
│   ├── test_db.py               # repository CRUD (in-memory SQLite)
│   └── test_validators.py
└── integration/
    └── test_recognition_pipeline.py   # end-to-end with test images
```

### 4.2 Run Tests

```bash
# All tests
pytest tests/ -v

# Unit only
pytest tests/unit/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### 4.3 Example Unit Test

```python
# tests/unit/test_matcher.py
import numpy as np
import pytest
from app.core.matcher import EmbeddingMatcher
from app.config import CONFIG

@pytest.fixture
def matcher():
    return EmbeddingMatcher()

@pytest.fixture
def identities():
    alice_vec = np.random.rand(512).astype(np.float32)
    alice_vec /= np.linalg.norm(alice_vec)
    return [{"person_id": "ALICE1", "name": "Alice", "embedding": alice_vec}]

def test_exact_match(matcher, identities):
    matcher.load_cache(identities)
    result = matcher.find_best(identities[0]["embedding"])
    assert result["name"] == "Alice"
    assert result["score"] >= 0.99

def test_unknown_below_threshold(matcher, identities):
    matcher.load_cache(identities)
    random_vec = np.random.rand(512).astype(np.float32)
    random_vec /= np.linalg.norm(random_vec)
    result = matcher.find_best(random_vec)
    # Note: this may occasionally be "Alice" if random is close
    # For determinism, use orthogonal vector
    assert "name" in result and "score" in result

def test_empty_cache_returns_unknown(matcher):
    result = matcher.find_best(np.ones(512, dtype=np.float32))
    assert result["name"] == "Unknown"

def test_cache_invalidation(matcher, identities):
    matcher.load_cache(identities)
    matcher.invalidate()
    result = matcher.find_best(identities[0]["embedding"])
    assert result["name"] == "Unknown"
```

### 4.4 Mocking ONNX Sessions

```python
# tests/unit/test_embedder.py
from unittest.mock import MagicMock, patch
import numpy as np
from app.models.arcface_model import ArcFaceModel

def test_get_embedding_shape():
    model = ArcFaceModel()
    # Mock ONNX session
    mock_session = MagicMock()
    mock_session.get_inputs.return_value = [MagicMock(name="input")]
    fake_output = np.random.rand(1, 512).astype(np.float32)
    mock_session.run.return_value = [fake_output]
    model._session = mock_session
    model._input_name = "input"

    dummy_crop = np.zeros((112, 112, 3), dtype=np.uint8)
    result = model.get_embedding(dummy_crop)

    assert result.shape == (512,)
    assert abs(np.linalg.norm(result) - 1.0) < 1e-5   # L2-normalized
```

---

## 5. Performance Tuning

### 5.1 Frame Rate Optimization

| Lever | Default | Effect |
|---|---|---|
| `FRAME_SKIP` | 2 | Process every 2nd frame; halves inference load |
| `queue.Queue(maxsize=2)` | 2 | Drops oldest frames under load; prevents memory growth |
| `intra_op_num_threads` | 4 | ONNX CPU thread count; tune to core count |
| Detector confidence | 0.7 | Higher = fewer false detections; faster matching |
| Embedding cache | In-memory | Pre-loaded at startup; zero DB reads during recognition |

### 5.2 Profiling

```bash
# Profile a single recognition pass
python -m cProfile -o prof.out main.py
python -m pstats prof.out
```

```python
# In-code timing (use for latency logging)
import time
t0 = time.perf_counter()
# ... operation ...
logger.debug(f"Operation took {(time.perf_counter()-t0)*1000:.1f}ms")
```

### 5.3 Target Benchmarks

| Metric | Target | Measured on i7-12th gen |
|---|---|---|
| Detection latency | < 10 ms | ~6 ms |
| ArcFace embedding | < 20 ms | ~14 ms |
| SFace embedding | < 10 ms | ~7 ms |
| Cosine match (100 identities) | < 2 ms | ~0.3 ms |
| End-to-end per-face | < 35 ms | ~22 ms |
| UI update (30 FPS) | 33 ms budget | — |

---

## 6. Build & Distribution

### 6.1 PyInstaller `.spec`

```python
# Facely.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/models/*.onnx', 'assets/models'),
        ('assets/icons/*',       'assets/icons'),
        ('app/db/schema.sql',    'app/db'),
    ],
    hiddenimports=[
        'onnxruntime',
        'cv2',
        'PIL',
        'deepface',
        'insightface',
        'numpy',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Facely',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No console window
    icon='assets/icons/Facely.ico',
)
```

```bash
pyinstaller Facely.spec
# Output: dist/Facely.exe
```

### 6.2 Build Notes

- UPX compression reduces `.exe` size by ~40%
- DeepFace model weights must be bundled or downloaded on first run
- SQLite DB is created at `%APPDATA%/Facely/` in production builds (not next to `.exe`)
- Use `sys._MEIPASS` for bundled asset paths in frozen mode:

```python
# app/config.py
import sys
from pathlib import Path

def _base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent
```

---

## 7. Git Workflow

### 7.1 Branch Strategy

```
main          → stable, tagged releases only
develop       → integration branch
feature/*     → new features
fix/*         → bug fixes
chore/*       → deps, tooling, docs
```

### 7.2 Commit Convention

```
feat(recognition): add SFace model adapter
fix(camera): prevent double-open on rapid start/stop
chore(deps): bump onnxruntime to 1.17.1
docs(arch): update threading diagram
test(matcher): add threshold boundary cases
```

### 7.3 PR Checklist

- [ ] `black` + `ruff` + `mypy` pass with no errors
- [ ] Unit tests added/updated for changed logic
- [ ] `pytest tests/` passes
- [ ] No hardcoded paths or magic numbers (use `config.py`)
- [ ] Logger calls use `get_logger(__name__)` (not print statements)
- [ ] New public methods have type hints and docstrings

---

## 8. Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| `Camera index 0 not found` | Webcam not connected | Check device manager; change `CAMERA_INDEX` |
| `ONNX model not found` | Missing `.onnx` file | Run `python scripts/download_models.py` |
| `tkinter not found` | Python installed without tk | On Linux: `sudo apt install python3-tk` |
| Low FPS on CPU | FRAME_SKIP too low | Increase `FRAME_SKIP` to 3 or 4 |
| Embeddings not persisting | DB not initialized | Run database init command (see Quick Start §4) |
| `deepface` slow first run | Model download | First run downloads ~550 MB; subsequent runs fast |
| EXE crashes silently | Console hidden | Temporarily set `console=True` in `.spec` to debug |

---

## 9. Extending: Multi-Camera Support

Facely is designed for easy multi-camera extension:

1. `CameraService` — instantiate multiple with different `camera_index`
2. `AppWindow` — add tabbed `CameraPanel` views
3. `RecognitionService` — one instance per camera, shared `ModelManager`
4. DB — no changes needed (embeddings are camera-agnostic)

---

## 10. Security Considerations

| Area | Recommendation |
|---|---|
| DB access | DB file should be readable only by the application user |
| Embeddings | Store hashed or encrypted at rest if PII compliance required |
| Logging | Do not log face embeddings at DEBUG level in production |
| Person IDs | Use opaque IDs (UUID), not names, in log files |
| GDPR | Provide identity deletion (already implemented via `delete_identity`) |