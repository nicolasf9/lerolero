#!/usr/bin/env bash
# Build LeroLero.app for macOS
set -e

cd "$(dirname "$0")/.."

echo "Building frontend..."
cd web && npm install && npm run build && cd ..

echo "Building macOS app..."
uv run pyinstaller \
    --noconfirm --onedir --windowed \
    --name "LeroLero" \
    --collect-all "lerolero" \
    --collect-all "webview" \
    --hidden-import "pynput.keyboard._darwin" \
    --hidden-import "pynput.mouse._darwin" \
    --paths "src" \
    --add-data "web/dist:lerolero/web_dist" \
    --add-data "src/lerolero/assets/icon.png:lerolero/assets" \
    --icon "src/lerolero/assets/icon.png" \
    --exclude-module "torch" \
    --exclude-module "openvino" \
    --exclude-module "transformers" \
    --exclude-module "scipy" \
    "src/lerolero/__main__.py"

echo ""
echo "Build complete: dist/LeroLero.app"
echo "To create DMG: hdiutil create -volname LeroLero -srcfolder dist/LeroLero.app dist/LeroLero.dmg"
