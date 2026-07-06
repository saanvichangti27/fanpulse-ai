#!/usr/bin/env bash
# FanPulse — start the LOCKED frontend wired to the real backend.
# Uses integration/craco.config.js (external seam); no file in frontend/ is
# touched. Requires the backend on :8000 first (scripts/run_backend.sh).
set -e
cd "$(dirname "$0")/../frontend"

if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies (yarn via corepack)..."
  corepack yarn install || {
    echo "corepack yarn failed — falling back to npm (resolutions are ignored by npm)."
    npm install --legacy-peer-deps
  }
fi

npx craco start --config ../integration/craco.config.js
