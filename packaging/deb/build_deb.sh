#!/bin/bash
# Script to create a Debian / Ubuntu .deb package
set -e

VERSION="1.2.0"
PKG_DIR="surfacemap-studio_${VERSION}_amd64"

rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/lib/surfacemap-studio"
mkdir -p "$PKG_DIR/usr/share/applications"

cat << CONTROL_EOF > "$PKG_DIR/DEBIAN/control"
Package: surfacemap-studio
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: amd64
Maintainer: ArkSentinel <arksentinel@users.noreply.github.com>
Description: Photometric PBR Material Texture Map Synthesizer
 SurfaceMap Studio converts single images into full PBR material sets
 (Normal, Height, Roughness, Metallic, AO, Specular, ORM Packed) with
 real-time 2D/3D previews, batch processing, and game engine export targets.
CONTROL_EOF

# Copy binary payload from dist if available
if [ -d "dist/surfacemap-studio" ]; then
    cp -r dist/surfacemap-studio/* "$PKG_DIR/usr/lib/surfacemap-studio/"
    ln -sf /usr/lib/surfacemap-studio/surfacemap-studio "$PKG_DIR/usr/bin/surfacemap-studio"
fi

cp packaging/linux/surfacemap-studio.desktop "$PKG_DIR/usr/share/applications/"

dpkg-deb --build "$PKG_DIR"
echo "Built surfacemap-studio_${VERSION}_amd64.deb successfully."
