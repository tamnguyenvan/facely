# Facely — Facial Recognition Desktop System

> Production-grade facial recognition GUI built with Python · PySide6 · ONNX · SQLite

---

![Facely Demo](./assets/facely-demo.gif)


## Overview

**Facely** is a modular, offline-first desktop application for real-time facial recognition. It supports three swappable inference backends — **ArcFace**, **DeepFace**, and **SFace** — with embedding-based identity matching, persistent storage, and a dark-theme professional GUI.

```
┌─────────────────────────────────────────────────────────┐
│  Camera Feed  │  Recognition Panel  │  Identity Sidebar │
│               │  Name + Confidence  │  Register / Manage│
│  [Live Feed]  │  [ArcFace ▼]        │  [Known Faces]    │
│               │  ● ONLINE           │  [Add / Delete]   │
└─────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Details |
|---|---|
| **Model Switching** | Hot-swap ArcFace / DeepFace / SFace at runtime |
| **Face Registration** | Capture → embed → store with name + ID |
| **Real-time Recognition** | Per-frame cosine similarity matching |
| **Confidence Display** | Name + score overlay; "Unknown" below threshold |
| **Embedding Store** | SQLite with BLOB storage, indexed by identity |
| **Logging** | Rotating file logs + structured console output |
| **Modular Design** | Clean separation: model layer / service layer / UI layer |

---

## Tech Stack

```
Language      Python 3.10+
GUI           PySide6 (Qt for Python)
AI Inference  ONNX Runtime (CPU / GPU)
Models        ArcFace, DeepFace, SFace - All ONNX format
Detection     Ultra-Light-Fast-Generic-Face-Detector-1MB
Camera        OpenCV (cv2)
Database      SQLite 3 via Python sqlite3
Similarity    NumPy cosine similarity
Logging       Python logging + RotatingFileHandler
Build         PyInstaller, Inno Setup, AppImage
```

---

## Quick Start

### Prerequisites

```bash
Python 3.10+
pip
A webcam
```

### Setup

```bash
git clone https://github.com/your-org/Facely.git
cd Facely

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download models (ArcFace, DeepFace, SFace, face detector)
python scripts/download_models.py

# Initialize database
python scripts/init_db.py

# Run
python main.py
```

Or use the automated setup script:

```bash
# Linux/Mac:
./setup_env.sh

# Windows:
setup_env.bat
```

---

## Models

| Model | Embedding Dim | File | Size |
|---|---|---|---|
| ArcFace | 512 | arcface.onnx | ~249 MB |
| DeepFace | 2622 | deepface.onnx | ~500 MB |
| SFace | 128 | sface.onnx | ~37 MB |
| Face Detector | - | version-RFB-640.onnx | ~1 MB |

Models are downloaded automatically via `scripts/download_models.py`.

---

## Configuration

All tuneable parameters live in `app/config.py`:

```python
# Camera
camera_index: int = 0
frame_width: int = 1280
frame_height: int = 720
frame_skip: int = 2

# Recognition
similarity_threshold: float = 0.55
default_model: str = "arcface"

# Paths
db_path: Path = "data/Facely.db"
model_dir: Path = "assets/models"
```

---

## Building

### Windows Installer

```bash
pip install pyinstaller innosetup
pyinstaller --clean --noconfirm Facely.spec
iscc build/installer.iss
# Output: build/Output/FacelySetup.exe
```

### Linux AppImage

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm Facely.spec
# Use linuxdeploy + appimagetool to create AppImage
```

See `docs/RELEASE.md` for CI/CD pipeline details.

---

## License

MIT © Facely Contributors