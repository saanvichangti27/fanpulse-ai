# FanPulse — start the LOCKED frontend wired to the real backend.
# Uses integration/craco.config.js (external seam); no file in frontend/ is
# touched. Requires the backend on :8000 first (scripts/run_backend.ps1).
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "frontend")

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies (yarn via corepack)..."
    corepack yarn install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "corepack yarn failed - falling back to npm (resolutions are ignored by npm)."
        npm install --legacy-peer-deps
    }
}

npx craco start --config ../integration/craco.config.js
