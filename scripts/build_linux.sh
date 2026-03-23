#!/usr/bin/env bash
# Build LeroLero for Linux
set -e

cd "$(dirname "$0")/.."

echo "Building frontend..."
cd web && npm install && npm run build && cd ..

echo "Building Linux binary..."
uv run pyinstaller \
    --noconfirm --onedir \
    --name "LeroLero" \
    --collect-all "lerolero" \
    --collect-all "webview" \
    --hidden-import "pynput.keyboard._xorg" \
    --hidden-import "pynput.mouse._xorg" \
    --paths "src" \
    --add-data "web/dist:lerolero/web_dist" \
    --add-data "src/lerolero/assets/icon.png:lerolero/assets" \
    --exclude-module "torch" \
    --exclude-module "openvino" \
    --exclude-module "transformers" \
    --exclude-module "scipy" \
    "src/lerolero/__main__.py"

echo ""
echo "Build complete: dist/LeroLero/"
echo ""
echo "Prerequisites for Linux users:"
echo "  sudo apt install xdotool libwebkit2gtk-4.0-dev"
