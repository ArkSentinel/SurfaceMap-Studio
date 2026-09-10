#!/bin/bash
# Script to package macOS application bundle
set -e

VERSION="1.2.0"
echo "Building SurfaceMap Studio for macOS..."

pyinstaller --noconfirm --onedir --windowed --name "SurfaceMap Studio" main.py

cd dist
zip -r "surfacemap-studio-macos-universal.zip" "SurfaceMap Studio.app"
echo "Generated dist/surfacemap-studio-macos-universal.zip successfully."
