# Assets Directory

This directory contains ONNX model files and other assets for Facely.

## Models Directory

Place your ONNX model files in `models/`:

### ArcFace
- **File:** `arcface.onnx`
- **Size:** ~249 MB
- **Source:** [facely-models](https://github.com/tamnguyenvan/facely-models)
- **URL:** https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/arcface.onnx

### DeepFace
- **File:** `deepface.onnx`
- **Source:** [facely-models](https://github.com/tamnguyenvan/facely-models)
- **URL:** https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/deepface.onnx

### SFace
- **File:** `sface.onnx`
- **Size:** ~37 MB
- **Source:** [facely-models](https://github.com/tamnguyenvan/facely-models)
- **URL:** https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/sface.onnx

### Face Detection (Ultra-Light-Fast-Generic-Face-Detector-1MB)
- **File:** `version-RFB-640.onnx`
- **Source:** [facely-models](https://github.com/tamnguyenvan/facely-models)
- **URL:** https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/version-RFB-640.onnx

## Download Models

Run the download script to fetch all models:

```bash
python scripts/download_models.py
```

## Model Format

All models must be in ONNX format (.onnx files).