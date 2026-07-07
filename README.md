# FanPulse AI

**Dominate the moment. Own the game.**

FanPulse AI is a real-time marketing intelligence platform for football. Sports
marketing today is reactive — by the time a brand launches a campaign, the moment
has passed. FanPulse listens to the roar of the crowd as a match unfolds — every
goal, red card, VAR controversy and full-time whistle — and instantly hands brands
ready-to-deploy, high-ROI marketing plays, while the emotion is still alive.

## Features

- **Live fan pulse** — ingests and classifies the live fan conversation (sentiment,
  emotion, topics, geography) as the match happens; the whole app updates in
  real time, no refresh needed.
- **Global emotion heatmap** — per-country live volume, sentiment and dominant
  emotion on an interactive world map.
- **Fan segmentation** — ML-clustered behavioral personas (Superfans, Traveling
  Ultras, Casual Streamers, Deal-Seekers, Lapsed Fans) with size, annual value,
  churn risk, preferred channel and data-derived traits.
- **Moments engine** — automatically detects match moments (goals, red cards, VAR,
  full-time) from spikes in fan conversation.
- **AI strategy cards** — every moment instantly generates targeted campaigns:
  segment × channel × AI-written ad copy × ROI projection, with benchmark-backed
  confidence scores and an expiry countdown.
- **Match demand prediction** — 0–100 ticket-demand index and sellout probability
  per fixture, re-forecast live when the match turns; real FIFA World Cup 2026
  knockout schedule.
- **Trending topics & live feed** — real-time hashtags and fan messages streaming
  alongside the match dashboard.

## Repository structure

```text
backend/       FastAPI app, ingestion pipeline, ML models, strategy/ROI engine
  app/         API routers, live match state, strategy & copy generation
  ingestion/   replay engine, NLP classification, analytics, YouTube connectors
  intelligence/demand forecast + fan segmentation models and training
frontend/      React app (Create React App + craco)
integration/   glue wiring the frontend to the backend (build config + data layer)
scripts/       one-command launchers and end-to-end smoke test
docs/          product spec, API contract, integration architecture
data/          replay fixtures, industry benchmarks, synthetic training datasets
```

## Setup

Prerequisites: **Python 3.11+**, **Node.js 18+** (with corepack, which ships with Node).

From the repo root:

```powershell
# 1. Backend environment
python -m venv backend/venv
backend/venv/Scripts/pip install -r requirements.txt      # macOS/Linux: backend/venv/bin/pip

# 2. Backend config
copy backend\.env.example backend\.env                    # macOS/Linux: cp backend/.env.example backend/.env
```

No API keys are required to run the app — it works fully out of the box on the
built-in replay engine. Optionally, add a `GEMINI_API_KEY` in `backend/.env` for
live LLM-written campaign copy (a curated playbook is used otherwise).

## Run

Two terminals, backend first:

```powershell
# Terminal 1 — backend API on http://localhost:8000
scripts\run_backend.ps1        # macOS/Linux: ./scripts/run_backend.sh

# Terminal 2 — frontend on http://localhost:3000 (installs deps on first run)
scripts\run_frontend.ps1       # macOS/Linux: ./scripts/run_frontend.sh
```

Then open **http://localhost:3000**.

Notes:

- First backend boot takes ~30–60 s (local NLP models loading); the match replay
  starts automatically and the app comes alive on its own.
- The very first page load can take a few seconds while the initial strategy
  cards are generated; after that, everything updates live every few seconds.
- Restarting the backend replays the match story from kickoff — every run is a
  fresh, reproducible demo.
