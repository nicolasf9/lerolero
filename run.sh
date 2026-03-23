#!/usr/bin/env bash
# Launch LeroLero on macOS/Linux
cd "$(dirname "$0")"

# Build React frontend if needed
if [ ! -d "web/dist" ]; then
    echo "Building frontend..."
    cd web && npm install && npm run build && cd ..
fi

# Launch
uv run lerolero "$@"
