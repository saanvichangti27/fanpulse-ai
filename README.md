# FanPulse AI

Real-time marketing intelligence for football. FanPulse watches fan reactions to a
match as they happen — goals, red cards, VAR, full-time — and turns each moment into
a ready-to-deploy marketing play, with live demand forecasting, fan segmentation, and
ROI simulation.

- **Backend** — FastAPI + SQLite, local NLP, trained ML models (demand forecast,
  fan segments), a deterministic strategy/ROI engine, and Gemini for copywriting.
- **Frontend** — the `emergent-ui` React app (Create React App + craco), rendered from
  real backend data. **It is locked** — see [docs/INTEGRATION.md](docs/INTEGRATION.md).

By default the app runs on the **fake replay engine** (synthetic fan comments), so you
can see the whole thing work end-to-end with no external accounts. Real YouTube
ingestion is available too (see [Data modes](#data-modes)).

---

## Prerequisites

- **Python 3.11+** (repo developed on 3.14)
- **Node.js 18+** (developed on 24) with **corepack** (ships with Node) for `yarn`
- No API keys required for the default demo. A Gemini key is optional (it only upgrades
  strategy-card copy; the app works fully without one — playbook templates are used as
  a fallback).

## First-time setup

From the repo root:

```powershell
# 1. Backend Python environment
python -m venv backend/venv
backend/venv/Scripts/pip install -r requirements.txt      # macOS/Linux: backend/venv/bin/pip

# 2. Backend config (the run script also does this automatically on first launch)
copy backend\.env.example backend\.env                    # macOS/Linux: cp backend/.env.example backend/.env
```

Frontend dependencies install automatically the first time you run the frontend script.
(To do it by hand: `cd frontend && corepack yarn install`.)

## Run the full app (with UI)

You need **two terminals**. Start the backend first — the frontend loads its data from it.

**Terminal 1 — backend** (FastAPI on `http://localhost:8000`):

```powershell
scripts\run_backend.ps1        # macOS/Linux: ./scripts/run_backend.sh
```

Wait until it prints `Application startup complete` and begins ingesting. The first boot
takes ~30–60 s while the local NLP models load. It auto-starts the synthetic replay, so
data begins flowing on its own — no manual step needed.

**Terminal 2 — frontend** (React dev server on `http://localhost:3000`):

```powershell
scripts\run_frontend.ps1       # macOS/Linux: ./scripts/run_frontend.sh
```

Then open **http://localhost:3000**. The four pages — Landing, Heatmap, Strategies,
Matches — all render live backend data.

Notes:
- The **very first** page load can take ~10 s while the backend generates the initial
  strategy cards. After that it's instant.
- The UI shows a **snapshot per page load** — refresh the browser to watch the match
  story advance (goals, moments, new campaigns). The locked UI does not auto-poll.
- Each backend restart **replays the match from the start** (a fresh, reproducible demo).
- The frontend never needs restarting when you change backend settings — just refresh.

## Data modes

The app can be fed from three sources; you switch by editing `backend/.env` and
restarting the backend. Full instructions and the exact `.env` blocks are in
[docs/INTEGRATION.md](docs/INTEGRATION.md).

| Mode | What it is | Needs a key? |
|---|---|---|
| **Synthetic replay** (default) | Hand-built fixture of fan comments with scripted goal/VAR/full-time beats — the full story | No |
| **Captured stream** | A real YouTube stream's chat, captured to a file and replayed | No |
| **Live stream** | Polls the live chat of a currently-live YouTube video in real time | Yes (YouTube Data API) |

To capture a finished stream's chat into a replay file:

```powershell
backend/venv/Scripts/python -m backend.ingestion.capture_youtube "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Verify the backend

A one-command end-to-end gate (cold start → replay → NLP → moments → campaigns →
forecast → UI bootstrap):

```powershell
backend/venv/Scripts/python scripts/smoke_test.py
```

## Project layout

```
backend/       FastAPI app, ingestion pipeline, ML models, strategy/ROI engine
  app/         API routers (incl. ui.py — the UI's data endpoint), match state, config
  ingestion/   replay engine, NLP, analytics, YouTube connector + capture
  intelligence/forecast + segmentation models and training
frontend/      LOCKED emergent-ui React app (do not edit)
integration/   the seam wiring the locked UI to the backend (craco config + data module)
scripts/       run_backend / run_frontend launchers, smoke test
docs/          spec, API contract, and INTEGRATION.md (how the wiring works)
data/          replay fixtures, benchmarks, synthetic/historical datasets
```

## Troubleshooting

- **Frontend page errors with "Could not reach the backend"** — start the backend first
  (Terminal 1) and wait for `Application startup complete`, then reload the page.
- **Port already in use** — something is already on `:8000` or `:3000`; stop it, or change
  the port (`--port` for uvicorn; `PORT=3001` for the frontend).
- **`yarn` not found** — enable it with `corepack enable`, or the run script falls back to
  `npm install`.
