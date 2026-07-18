# Facely Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- Webcam
- pip package manager

## Installation

### 1. Create Virtual Environment

```bash
python -m venv .venv

# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Models

```bash
python scripts/download_models.py
```

This downloads all required ONNX models to `assets/models/`:
- `arcface.onnx` - ArcFace (~249 MB)
- `deepface.onnx` - DeepFace
- `sface.onnx` - SFace (~37 MB)
- `version-RFB-640.onnx` - Face detector

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Create Required Directories

```bash
mkdir -p data
mkdir -p logs
```

## Running the Application

```bash
python main.py
```

## First Time Usage

1. The application will start with the camera inactive
2. Click "▶ Start Camera" to begin
3. To register a face:
   - Enter a name in the "Register Face" section
   - Optionally enter a custom ID
   - Click "● Capture" while facing the camera
   - The system will capture 5 frames automatically
4. Registered faces will appear in the "Known Identities" list
5. The camera will recognize registered faces in real-time

## Switching Models

Use the "Model" dropdown in the control panel to switch between:
- arcface (default, 512-dim embeddings)
- deepface (2622-dim embeddings)
- sface (128-dim embeddings)

## Troubleshooting

### Camera Not Found
- Check that your webcam is connected
- Try changing `camera_index` in `app/config.py`

### Model Load Error
- Run `python scripts/download_models.py` to re-download
- Check that files exist in `assets/models/`

### Database Error
- Run `python scripts/init_db.py` to reinitialize
- Check that `data/` directory exists

## Configuration

Edit `app/config.py` to customize:
- Camera settings (resolution, index)
- Recognition threshold
- Frame skip rate
- Logging level

## Logs

Application logs are stored in:
- `logs/Facely.log` - All logs
- `logs/Facely_error.log` - Errors only

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```