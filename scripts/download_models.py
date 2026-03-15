#!/usr/bin/env python3
"""
Script to download required ONNX model files for Facely.
"""
import urllib.request
import os
from pathlib import Path

MODELS_DIR = Path("assets/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODELS = {
    "arcface.onnx": "https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/arcface.onnx",
    "deepface.onnx": "https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/deepface.onnx",
    "sface.onnx": "https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/sface.onnx",
    "version-RFB-640.onnx": "https://github.com/tamnguyenvan/facely-models/releases/download/v0.0.1/version-RFB-640.onnx",
}


def download_file(url: str, dest: Path) -> None:
    """Download a file with progress indicator."""
    print(f"Downloading {dest.name}...")
    urllib.request.urlretrieve(url, dest)
    print(f"  Saved to {dest}")


def main():
    print("Facely Model Downloader")
    print("=" * 50)

    for filename, url in MODELS.items():
        dest = MODELS_DIR / filename
        if dest.exists():
            print(f"  {filename} already exists, skipping")
        else:
            download_file(url, dest)

    print("\nAll models downloaded successfully!")


if __name__ == "__main__":
    main()