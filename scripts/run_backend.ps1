# FanPulse — start the backend (FastAPI + fake replay engine) on :8000
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path "backend/.env")) {
    Copy-Item "backend/.env.example" "backend/.env"
    Write-Host "Created backend/.env from .env.example (add GEMINI_API_KEY for live LLM copy; playbook fallback works without it)."
}

$venvPython = Join-Path $root "backend/venv/Scripts/python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

& $python -m uvicorn backend.app.main:app --port 8000
