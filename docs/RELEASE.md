# Release Guide

This document describes how to create releases for Facely.

## Prerequisites

1. Icon files in `build/` directory:
   - `facely.ico` (Windows)
   - `facely.png` (Linux, 256x256)

2. GitHub repository with Actions enabled

3. LICENSE file in repository root

## Release Process

### Automated Release (Recommended)

1. Update version in `setup.py`
2. Commit changes:
   ```bash
   git add setup.py
   git commit -m "Bump version to X.Y.Z"
   ```

3. Create and push tag:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

4. GitHub Actions will automatically:
   - Build AppImage for Linux
   - Build installer for Windows
   - Create GitHub release with artifacts

### Manual Build

#### Linux AppImage

```bash
# Install dependencies
pip install -r requirements.txt pyinstaller

# Download models
python scripts/download_models.py

# Build with PyInstaller
pyinstaller --clean --noconfirm Facely.spec

# Create AppImage (requires linuxdeploy and appimagetool)
mkdir -p AppDir/usr/bin
cp -r dist/Facely/* AppDir/usr/bin/
cp build/Facely.desktop AppDir/usr/share/applications/
cp build/facely.png AppDir/usr/share/icons/hicolor/256x256/apps/
appimagetool AppDir Facely-x86_64.AppImage
```

#### Windows Installer

```bash
# Install dependencies
pip install -r requirements.txt pyinstaller

# Download models
python scripts/download_models.py

# Build with PyInstaller
pyinstaller --clean --noconfirm Facely.spec

# Create installer (requires Inno Setup)
iscc build/installer.iss
```

## Build Outputs

- Linux: `Facely-x86_64.AppImage`
- Windows: `build/Output/FacelySetup.exe`

## Testing Releases

Before creating a release:

1. Test the build locally on target platform
2. Verify all dependencies are included
3. Test installation and uninstallation
4. Check application launches correctly
5. Verify models are bundled and load properly

## Troubleshooting

### Missing Dependencies

If the built application fails to run, check:
- PyInstaller spec includes all hidden imports
- Data files (models, SQL schema) are bundled
- System libraries are available on target system

### AppImage Issues

- Ensure FUSE is available on target Linux system
- Test on clean Ubuntu 20.04 or later
- Check AppImage permissions: `chmod +x Facely-x86_64.AppImage`

### Windows Installer Issues

- Verify Inno Setup is installed
- Check icon file paths in installer.iss
- Test on clean Windows 10/11 system
- Ensure Visual C++ Redistributable is available
