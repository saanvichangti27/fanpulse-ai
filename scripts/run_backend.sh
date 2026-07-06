#!/usr/bin/env bash
# FanPulse — start the backend (FastAPI + fake replay engine) on :8000
set -e
cd "$(dirname "$0")/.."

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env from .env.example (add GEMINI_API_KEY for live LLM copy; playbook fallback works without it)."
fi

PY=backend/venv/Scripts/python.exe
[ -x "$PY" ] || PY=backend/venv/bin/python
[ -x "$PY" ] || PY=python

"$PY" -m uvicorn backend.app.main:app --port 8000
