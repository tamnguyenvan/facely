# Build Assets

This directory contains build configuration files for packaging Facely.

## Files

- `installer.iss` - Inno Setup script for Windows installer
- `Facely.desktop` - Linux desktop entry file
- `facely.ico` - Windows application icon (add this file)
- `facely.png` - Linux application icon (add this file, 256x256 recommended)

## Icon Requirements

You need to add icon files:
- `facely.ico` - Windows icon (multi-resolution .ico file)
- `facely.png` - Linux icon (256x256 PNG recommended)

You can create these from a source image using tools like:
- ImageMagick: `convert icon.png -resize 256x256 facely.png`
- Online converters for .ico format
