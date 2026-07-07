# FanPulse AI — Frontend ⇄ Backend Integration

**Status:** final integrated version. The `emergent-ui` frontend is wired end-to-end
to the real backend, driven (for now) by the **fake replay engine** with synthetic
comments — the live-YouTube path is intentionally not enabled yet.

**The frontend is LOCKED.** Every file under `frontend/` is byte-for-byte identical
to the `emergent-ui` branch. Verify anytime:

```bash
git diff emergent-ui HEAD -- frontend   # must print nothing
```

---

## 1. How the wiring works (zero frontend edits)

The locked UI never calls the network itself — every page imports its datasets from
a single module, `@/data/mock` (`frontend/src/data/mock.js`). That module is the
integration seam:

```
frontend (LOCKED)                    integration/ (ours)                backend
─────────────────                    ───────────────────               ─────────
import {...} from "@/data/mock" ──►  craco.config.js alias             FastAPI :8000
                                     "@/data/mock$" ──► live-data.js ──► GET /api/v1/ui/bootstrap
                                     (sync XHR before first render)      (all datasets, real engines)
```

- `integration/craco.config.js` loads the frontend's own CRACO config untouched and
  adds **one exact-match webpack alias**: the `"@/data/mock"` request resolves to
  `integration/live-data.js`. (It also drops CRA's ModuleScopePlugin, which forbids
  imports from outside `frontend/src` — our module deliberately lives outside.)
- `integration/live-data.js` fetches `/api/v1/ui/bootstrap` **synchronously** at
  module-evaluation time (the UI reads the exports before the first React render,
  so the data must exist by then) and re-exports the identical names/shapes:
  `BRAND, NAV_LINKS, KPI_TICKER, FEATURES, FAN_SEGMENTS, COUNTRIES, INDUSTRIES,
  LOCATIONS, STRATEGIES, MATCHES, SENTIMENT_TIMELINE, MOMENTS, TRENDING`.
- **Live updates (no reload):** `live-data.js` re-polls the bootstrap every 4 s
  (skipping unchanged payloads) and `integration/live-app.js` — aliased over
  `"@/App$"` — wraps the locked `<App/>` in a `useSyncExternalStore`
  subscription, re-rendering the tree in place whenever fresh data lands.
  Feed, strategies, scores, clock and trending all move with the match.
- Launched via `npx craco start --config ../integration/craco.config.js`
  (wrapped in `scripts/run_frontend.*`). Running plain `yarn start` inside
  `frontend/` still uses the bundled mock module — the friend's app remains fully
  standalone and untouched.

If the backend is down, the page fails **loudly** with instructions (no silent
fallback to mock data — nothing fake is ever displayed).

## 2. Run it

```powershell
# 1. backend (FastAPI on :8000 — seeds DB, auto-starts the fake replay)
scripts\run_backend.ps1        # or ./scripts/run_backend.sh

# 2. frontend (CRA dev server on :3000, wired through the integration seam)
scripts\run_frontend.ps1       # or ./scripts/run_frontend.sh
```

The first-ever page load can take ~10 s: the backend generates the initial
strategy cards (one real Gemini call; the rest use the playbook fallback until the
debounce clears). Subsequent loads are instant, and the app **updates itself every ~4 s**
(no refresh needed) as the replay/moments advance.

Backend env knobs (see `backend/.env.example`): `DEMO_MATCH_ID`, `REPLAY_AUTOSTART`,
`REPLAY_FILE`, `REPLAY_SPEED`, `REPLAY_LOOP`, `REPLAY_RESET_ON_START`,
`REPLAY_TIME_SCALE`, `CORS_ORIGINS`, `AUTO_CAMPAIGN_INDUSTRIES`, `GEMINI_API_KEY`.

## 3. Backend changes made for the integration

Everything below is on `main`, backend/integration only. **No file in `frontend/`
was created, edited, or deleted.**

### New

| File | What it does |
|---|---|
| `backend/app/routers/ui.py` | `GET /api/v1/ui/bootstrap` — BFF endpoint assembling every UI dataset (shapes match `mock.js` 1:1) from the real engines |
| `backend/app/ui_meta.py` | Static reference tables: country ISO2→ISO3/name/flag/coords, team short-codes/flags, stage labels, event-tag display strings, industry slug↔UI-id map, segment colors, app copy |
| `backend/app/match_state.py` | Live match state from replay moments: kickoff→`live`+clock start, goal→score (attributed to the side whose fan country dominates the live 1-min window), full_time→`finished`; plus **auto-reforecast** on goal/red-card/VAR/full-time (persists a real model reforecast — powers the UI's "Δ Forecast") |
| `integration/craco.config.js`, `integration/live-data.js` | The wiring seam (see §1) |
| `scripts/run_backend.ps1/.sh`, `scripts/run_frontend.ps1/.sh` | One-command launchers |

### Modified

| File | Change |
|---|---|
| `backend/app/main.py` | CORS middleware (frontend origin); `ui` router; SQLite additive migration for new match columns; optional demo reset at boot (`REPLAY_RESET_ON_START`, default true — every boot retells the match fresh); replay **autostart** (`REPLAY_AUTOSTART`, default true — no manual `POST /replay/control` needed) |
| `backend/app/models_db.py` | `matches` gains `home_score`, `away_score`, `clock_started_at` |
| `backend/app/automation.py` | `on_moment` now also applies match-state updates (score/clock/status + auto-reforecast) before auto-campaigns, independent of `AUTO_CAMPAIGN_INDUSTRIES` |
| `backend/ingestion/replay.py` | Optional `loop` mode (re-suffixes `external_id` per pass so the DB's dedupe doesn't drop repeats) |
| `backend/app/gemini_client.py` | Fallback copy for **content-creator** campaigns: those playbook entries use the ContentIdea shape (`format/hook/concept`), which previously produced an empty headline/body/cta card; now mapped onto the Copy shape |
| `backend/.env.example` | New demo/integration env vars documented |

### New backend features built because the frontend displays them

- **Match scores + live minute + status transitions** — the UI shows `2–1 67'`;
  the backend had no score concept. Now derived from replay moments (goal
  attribution rule documented in `match_state.py`; the synthetic fixture doesn't
  encode the scorer, so celebrating-fans-country decides, defaulting to home).
- **Automatic live reforecast** — the UI's F.04 feature card promises
  "re-forecast live when the match turns" and the match screen shows
  "Δ Forecast" vs baseline. Previously reforecasts only happened via a manual
  endpoint; now every goal/red-card/VAR/full-time moment persists a real
  momentum-driven model reforecast.
- **Bootstrap baseline strategy cards** — the strategies screen crashes on an
  empty list (`STRATEGIES[0]`), so on a fresh boot the backend generates one real
  baseline campaign per starred industry through the same engine path as the
  manual endpoint (trigger `bootstrap_baseline`). Moment-triggered auto-campaigns
  then replace them organically.

## 4. Dataset mapping (UI export → real source)

| UI export | Source |
|---|---|
| `BRAND`, `NAV_LINKS`, `FEATURES` | static app copy (`ui_meta.py`) — not data |
| `KPI_TICKER` | `analytics.get_kpis` (demo match) + live-match count + latest campaign ROAS vs baseline uplift |
| `FAN_SEGMENTS` | KMeans segment profiles (`intelligence/segments`); colors are presentation constants |
| `COUNTRIES` | `analytics.get_heatmap` (volume, dominant emotion, avg sentiment rescaled −1..1 → 0..1) + `ui_meta` coords/names; country→segment attribution = first KMeans segment listing the country in its `top_countries` (fallback: largest segment); GB/UK merge to ENG |
| `INDUSTRIES`, `LOCATIONS` | starred industries (UI ids); "Global" + countries seen live |
| `STRATEGIES` | `campaigns` table (strategy engine + ROI funnel + Gemini/playbook copy). `multipliers.total`=M, `roi`=real funnel, `confidence`=data-support score, `ai_generated`=¬`llm_fallback`, `ends_in_min`=live remaining window |
| `MATCHES` | matches table + GBR forecast (baseline & latest persisted reforecast), scores/minute from `match_state`, excitement = live momentum score, else model buzz×100 |
| `SENTIMENT_TIMELINE` | `analytics.get_timeline` 30-s buckets → match minutes via `REPLAY_TIME_SCALE` (fixture compresses 90' into ~800 s) |
| `MOMENTS` | `moments` table (event tag → the exact display strings the UI's icon map keys on) |
| `TRENDING` | `analytics.get_topics` (note: the UI never renders this export — see §5) |

## 5. Backend/product features the frontend does NOT display (report only — frontend untouched)

Per instruction, nothing was added to the UI for these; listed for a later call:

1. **`TRENDING` is a dead export** — mock.js exports it, we serve it, but no page imports it.
2. **`KPI_TICKER` is never rendered** — `components/Ticker.jsx` exists in the locked
   frontend but no page or layout mounts it. We serve fully real ticker values
   (mentions, sentiment, excitement, live-match count, ROI uplift) that appear
   nowhere; wiring `<Ticker/>` into `Layout.jsx` would be a one-line frontend
   change — **not done** (frontend locked).
4. **Strategy card fields served but never rendered:** `variant_b` (A/B copy), `multipliers` breakdown, `window_min`, `ai_generated` flag, `trigger.type`/`moment_id` (only `trigger.desc` shows).
5. **Match fields served but never rendered:** `drivers` (forecast feature importances), `forecast_trigger`, `venue.capacity`.
6. **Moment fields not rendered:** `volume`, `emotion` (icon color comes from `type`).
7. **Whole backend features with no UI surface:** live message feed (`/matches/{id}/feed`), topics endpoint, content-idea generator (`/content/generate`), next-best-actions matrix (`/fans/next-best-actions`), ROI simulator + media planner (`/roi/*`), manual reforecast endpoint, replay control endpoint, health endpoint, the 10 non-starred industries, per-segment live `activity_share_pct` overlay.
8. **Hardcoded UI copy that doesn't come from data (in the locked frontend):** the heatmap page shows a fixed "silhouette score · 0.62" label — the real trained value is **0.34** (served in the segments report but the label is a string literal in `Heatmap.jsx`). Same for the footer "Frontend Preview" wording and the timeline's "5-min buckets" caption (real buckets are 30 s scaled to match-minutes).
9. **`SENTIMENT_TIMELINE` is global in the UI** — one export shared by all matches (mock behaved the same way); we serve the demo match's timeline, so selecting other fixtures shows the demo match's curve.
10. **Sub-1.0 ROAS is real** — mock showed 2.8–6.2× everywhere; actual benchmark funnels at baseline (M=1) can be < 1×. Cards lift when moments fire (M up to 2.5).

## 6. Known trade-offs

- **Synchronous bootstrap XHR** blocks first paint until the backend responds
  (sub-second warm, ~10 s on the very first boot while initial cards generate).
  The only alternative was editing the frontend — off the table.
- **Replay clock is wall-clock scaled**: restarting the backend resets the story
  (`REPLAY_RESET_ON_START=true`) so every demo run is reproducible.
- The YouTube connector, capture scripts and `SOURCES=youtube` path are untouched
  and off by default — switching to the real ingestion later is config-only.

## 7. Later additions (post-integration)

- **Dynamic updates**: see §1 — the integration layer polls and re-renders; no frontend file was changed for this.
- **Real WC2026 schedule**: `backend/app/seed.py` seeds the real knockout fixtures around 2026-07-07 (sources: FIFA/Al Jazeera/ESPN, fetched 2026-07-07); the seeder auto-reseeds when the fixture list changes. The demo/replay match is m_001 (Argentina vs Egypt, R16).
- **Concurrent replay files**: `REPLAY_FILE` accepts a comma-separated list with optional per-file speed (`file:speed`); the simulated Twitter stream (`replay_twitter_sim.json`, regenerated for ARG-EGY) runs alongside the main stream, so trending topics carry real sim hashtags (kept with their `#` by the NLP topic extractor).
- **`AUTO_KICKOFF=true`** (optional): flips a still-upcoming match to LIVE on first real ingestion — for captured/live streams without a scripted kickoff marker.
