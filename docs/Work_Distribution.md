# FanPulse AI — Work Distribution
### Three parallel workstreams, designed for AI-agent execution in a ~10-hour build
*Companion to `FanPulse_AI_Product_Spec.md` (the WHAT) and `API_Contract.md` v3.0.0 (the interfaces). Matches the hackathon-minimal architecture: **one FastAPI process, one SQLite file, no WebSocket, no Redis, no Docker, no migrations. Analytics are SQL at read time.***

---

## 0. Instructions for the AI agents

You are one of three build agents. Each owns exactly one workstream.

1. Build **only** inside your owned paths (§2). Never edit another workstream's files.
2. `docs/API_Contract.md` and `backend/contracts.py` are **frozen law**. If your work seems to need a contract change, STOP and ask the humans.
3. **This is a hackathon demo built by a small team on a hard time limit — not a production app.** The bar is: every feature works end-to-end and its output looks complete. Prefer the dumbest thing that satisfies the contract. Concretely banned: WebSockets/SSE, Redis, message queues, Docker, Alembic, caching layers, retry frameworks, class hierarchies where a function does, config systems beyond `.env`, and any abstraction "for later."
4. **No frontend work.** Swagger UI (`/docs`) + `scripts/smoke_test.py` are the test surface. Do not install Node.
5. Meet your Definition of Done, then stop. Stretch items only after the smoke test is green on `main`.

**Precedence:** `API_Contract.md` > this document > `FanPulse_AI_Product_Spec.md`. The old Build Bible is superseded.

---

## 1. Workstreams and seams

| Workstream | Owner | Scope (spec §4 features) | Boundary |
|---|---|---|---|
| **W1 · Ingestion & Live Analytics** | **R S Raksha** | Feature 1 (Reddit connector, local NLP, analytics functions, moment loop) + Replay Engine + Feature 2's data | Writes `messages`/`moments` rows; implements the §E analytics functions + `run_ingestion` + `ReplayController`. No API code, no Gemini. |
| **W2 · Backend & Recommendation Engine** | **Saanvi C** | FastAPI app, DB models/seed, all REST endpoints + Feature 5 (strategy engine, playbook, Gemini copy) | Serves contract §B. Calls W1's §E functions and W3's §F functions. |
| **W3 · Predictive Intelligence** | **Raksha S** | Feature 3 (forecast + re-forecast), Feature 4 (synthetic CRM, KMeans, engagement, NBA), Feature 6 (ROI funnel, multiplier, planner) + all datasets | Pure-Python `backend/intelligence/` implementing contract §F. sklearn only; no FastAPI/DB/async. |

```
FastAPI app (W2) ──imports/calls──► intelligence/ (W3, pure functions over committed data)
     │  ▲
     │  └── endpoints call ingestion/analytics.py (W1) = SQL over SQLite
     └── startup: asyncio task run_ingestion(on_moment=W2 auto-campaign fn) (W1)
                          │
                          └── writes messages/moments rows to SQLite
```

- W1 ⇄ W2: SQLite tables + the function signatures in contract §E. W1 imports `app.models_db`, `app.db`, `contracts` only.
- W3 ⇄ W2: contract §F signatures. W3 imports `contracts` only.
- W1 ⇄ W3: never directly.

**Git:** branches `ws1-ingestion`, `ws2-backend`, `ws3-intelligence`; merge at phase gates (§6). `main` must pass `scripts/smoke_test.py`.

---

## 2. Repository structure & ownership

```
fanpulse-ai/
├── docs/                              # frozen (humans only)
├── backend/
│   ├── contracts.py                   # OWNER: Saanvi — Phase 0, == contract §A + §B response
│   │                                  #   models, verbatim; then FROZEN
│   ├── app/                           # OWNER: Saanvi
│   │   ├── main.py                    # startup: create_all → seed if empty → start
│   │   │                              #   run_ingestion task (on_moment = auto-campaign fn)
│   │   ├── config.py                  # .env loading (a few os.getenv calls are fine)
│   │   ├── db.py                      # engine/session (sqlite:///fanpulse.db)
│   │   ├── models_db.py               # SQLAlchemy == contract §D verbatim (6 tables)
│   │   ├── seed.py                    # 6 fixture matches + a few sample rows per table
│   │   ├── routers/                   # matches.py, fans.py, campaigns.py, predictions.py,
│   │   │                              #   roi.py, replay.py
│   │   ├── strategy/
│   │   │   ├── engine.py              # deterministic WHO/WHEN/WHERE/WHAT (spec §7.1)
│   │   │   └── playbook.py            # PLAYBOOK dict per contract §G.1 (archetype, window,
│   │   │                              #   tone_notes, template = fallback copy)
│   │   └── gemini_client.py           # one function: brief → copy JSON; debounce, cache,
│   │                                  #   on failure fill the playbook template (llm_fallback)
│   ├── ingestion/                     # OWNER: Raksha R
│   │   ├── service.py                 # run_ingestion + moment loop + ReplayController (§E.2)
│   │   ├── analytics.py               # get_kpis/timeline/heatmap/topics/momentum/
│   │   │                              #   country_volumes (§E.1) — SQL over messages
│   │   ├── nlp.py                     # sentiment + emotion pipelines (local, batched)
│   │   │                              #   + topics = watchlist ∪ word-frequency (NO KeyBERT)
│   │   ├── geo.py                     # country: replay field → subreddit map → None
│   │   ├── reddit_connector.py        # CORE live source (PRAW, poll 20 s, dedupe, log errors)
│   │   ├── youtube_connector.py       # STRETCH — only after smoke test is green
│   │   ├── news_connector.py          # STRETCH
│   │   └── replay.py                  # replay_engine + capture script (§E.3 file schema)
│   ├── intelligence/                  # OWNER: Raksha S
│   │   ├── data_gen/                  # gen_fans.py, gen_history.py
│   │   ├── forecast.py                # §F.1 (+ train_forecast.py → artifacts/)
│   │   ├── segments.py                # §F.2 (+ train_segments.py → artifacts/)
│   │   ├── roi.py                     # §F.3 (funnel + multiplier + planner in one module)
│   │   └── artifacts/                 # committed pickles + metrics.json + feature_importance.json
│   ├── requirements.txt               # append-only; announce additions
│   └── .env.example                   # GEMINI_API_KEY, REDDIT_*, SOURCES=replay,
│                                      #   AUTO_CAMPAIGN_INDUSTRIES=food_delivery,merch_apparel
├── data/
│   ├── replay/                        # OWNER: Raksha R — replay_dev_fixture.json (+ real capture)
│   ├── synthetic/fans.csv             # OWNER: Raksha S
│   ├── historical/matches_history.csv # OWNER: Raksha S
│   └── benchmarks/                    # OWNER: Raksha S — benchmarks.csv, emotion_brand_fit.csv
└── scripts/
    └── smoke_test.py                  # OWNER: Saanvi — THE integration gate (contract §H)
```

Local dev = `pip install -r requirements.txt` → `uvicorn app.main:app`. Nothing else to run or install.

---

## 3. W1 — R S Raksha: Ingestion & Live Analytics (Feature 1 + Replay)

**Mission:** raw fan text → classified rows → on-demand analytics → moment events. You never call Gemini, never build endpoints, never make marketing decisions. Ingestion is deliberately dumb: *poll → classify → insert row*. All intelligence about the stream lives in `analytics.py` as SQL at read time.

**Build order:**

1. **Replay first** (`replay.py` + `data/replay/replay_dev_fixture.json`): hand-write ~200 messages (`source="replay"`) with `goal` / `var_controversy` / `full_time` markers per contract §E.3. `replay_engine` feeds items through the same classify→insert path as live data, at a speed multiplier; `ReplayController.start/stop`. Later, if time: run `capture.py` (same connectors, dump to JSON) during any real match for a real captured file.
2. **NLP** (`nlp.py`): the two local pipelines loaded once (`cardiffnlp/twitter-roberta-base-sentiment-latest`, `j-hartmann/emotion-english-distilroberta-base`), batch size 16–32. **Topics = watchlist matching** (team rosters from seed + {var, referee, penalty, red card, goal}) **plus top non-stopword tokens — no KeyBERT, no sentence-transformers.** Arousal always via `contracts.AROUSAL`.
3. **Analytics** (`analytics.py`): the six §E.1 functions as straightforward SQL/pandas over `messages` (+ `moments` for timeline tags). KPI excitement uses the frozen §A.3 formula. `get_momentum` returns `None` when `volume_5m < MOMENTUM_MIN_MESSAGES_5M`.
4. **Moment loop + service** (`service.py`): implements contract §E.2 — poll sources, classify, insert; every 10 s check the moment rule (3× volume + 10pp swing, 120 s cooldown), classify the tag (§E.2 heuristics; replay markers force it), insert the `moments` row, `await on_moment(event)` with the callback's errors caught.
5. **Reddit connector**: PRAW script app, poll configured subreddits every 20 s, in-memory seen-set + DB UNIQUE as dedupe, log-and-continue on every error. **YouTube/news: stretch only.**

**Definition of Done:** replay run fills `messages` + `moments` from cold start; all six analytics functions return contract-valid shapes during it; goal beat fires exactly one `goal` moment; `SOURCES=reddit` streams real comments through the same path; killing the network mid-replay changes nothing.

---

## 4. W2 — Saanvi C: Backend & Recommendation Engine (Feature 5)

**Mission:** the app spine + the Feature-5 brain. You go first.

**Phase 0 (others are gated on it — keep it to a few files, no cleverness):** `contracts.py` (contract §A + §B response models verbatim) · `models_db.py` (§D) · `db.py` · `seed.py` (6 matches + sample rows so every endpoint answers immediately) · commit to `main`, announce.

**Build order:**

1. **Endpoints** (contract §B): thin routers — hot reads call W1's `analytics.py`; history reads query SQLite; intelligence reads call §F functions. Until the others land, use two tiny stubs you write: `stubs_intelligence.py` (contract-valid dummies, env `USE_INTELLIGENCE_STUBS=true`) and `scripts/fake_moment.py` (inserts messages simulating a joy spike so the moment loop fires without W1).
2. **Playbook** (`strategy/playbook.py`): the `PLAYBOOK` dict per contract §G.1 — full rows for the 5 starred industries × 7 emotions, `(*, industry)` `brand_awareness` fallback for the rest. Each row's `template` doubles as the Gemini-failure fallback copy.
3. **Strategy engine** (`strategy/engine.py`, spec §7.1): WHO = best segment by `industry_affinity × country_overlap × avg_engagement_score` (or the requested one) · WHEN = playbook window from the moment timestamp · WHERE = `intelligence.roi.best_channel` (or playbook default) · WHAT = playbook archetype. Attach `simulate_roi` (live + baseline) and assemble the §B.7 evidence block from momentum + segment stats + multiplier breakdown. Deterministic — no LLM here.
4. **Gemini client** (`gemini_client.py`): one function `generate_copy(brief) -> dict` — `gemini-2.5-flash`, strict JSON per §G.3, debounce ≥ 12 s, cache by `(match, archetype, industry, segment)`, **any failure → fill the playbook template's slots, `llm_fallback: true`**. Content flavour = same call with the content schema.
5. **Auto-campaign callback**: the `on_moment` function passed into `run_ingestion` — strategy engine for `AUTO_CAMPAIGN_INDUSTRIES`, persist campaign rows. The demo catches them by polling `GET .../campaigns`.
6. **`scripts/smoke_test.py`** exactly per contract §H.

**Definition of Done:** every §B endpoint returns response-model-valid JSON on seed data alone; Swagger renders all of it; a fake moment produces a persisted campaign with full evidence + real Gemini copy in < 15 s; Gemini blocked → template fallback with `llm_fallback: true`; smoke test green from cold start with one command.

---

## 5. W3 — Raksha S: Predictive Intelligence (Features 3, 4, 6)

**Mission:** every predicted number, as pure seeded functions over committed data. sklearn only — **no xgboost**. No FastAPI/DB/async imports anywhere in the package.

**Build order:**

1. **Fan CRM** (`data_gen/gen_fans.py` → `data/synthetic/fans.csv`, 5,000 rows, 16 columns: `fan_id, age, gender, country_code, favourite_team, matches_attended, tickets_bought_24m, avg_ticket_spend_usd, merch_purchases_12m, merch_spend_usd_12m, app_sessions_30d, email_open_rate, push_opt_in, days_since_last_engagement, streaming_minutes_30d, social_shares_30d, preferred_channel`). **Persona-first sampling** (document in the docstring — it is the defense against "random numbers"): 5 personas with hardcoded distribution params — Superfan 8% (attendance ~Poisson(6), merch ~LogNormal(μ=5.8), short recency-gap), Traveling Ultra 7% (highest attendance/spend), Casual Streamer 35% (no attendance, high streaming), Deal-Seeker 30% (low spend, push opt-in ~0.9, high sessions), Lapsed Fan 20% (recency-gap ~Exp(200)). Sample persona → sample features → noise → **drop the persona column** so KMeans honestly re-discovers it.
2. **Segments** (`segments.py` + `train_segments.py`): StandardScaler → KMeans k=5 → map clusters to the §A slugs by centroid rules → save pickles + `segment_profiles.json` (incl. silhouette, honestly). Engagement = RFM-D percentiles, weights 0.25×4. NBA per (segment × starred industry): channel (preference ∩ best benchmark ROI), archetype, timing rule, `expected_ctr` = benchmark CTR × affinity, one-line rationale.
3. **Forecast** (`forecast.py` + `train_forecast.py`): `data/historical/matches_history.csv` from **real public data** (Kaggle FIFA World Cup attendance + Wikipedia tables; URLs in docstring). Features = `MatchFeatures`; target `attendance_pct` (clip 1.05). Training `buzz_index` = documented formula `clip(0.40·stage_norm + 0.25·rivalry + 0.20·(1−rank_gap_norm) + 0.15·host_involved + N(0,0.05), 0, 1)`; inference = `compute_live_buzz(momentum)` (§F.1). Model: sklearn `GradientBoostingRegressor`, 80/20 holdout, MAE → `artifacts/metrics.json`, importances → `feature_importance.json`. `reforecast` must move +5..+20 points on goal-level momentum.
4. **ROI** (`roi.py`): funnel formulas (spec §6.1) returning every intermediate number; multiplier per §A.3 constants (`MomentStrength = clip(volume_ratio/3, 0, 1)`; SegmentMatch formula documented in the docstring; `momentum=None` ⇒ M=1.0); planner = allocate ∝ `demand_index × expected_M`, greedy, 60% cap, rationale strings; confidence per §F.3. **Datasets:** `benchmarks.csv` (`industry, channel, cpm_usd, ctr, cvr, aov_usd, frequency, source, source_url`) — cited rows for the 5 starred industries, one `source="interpolated"` default row per unstarred industry; `emotion_brand_fit.csv` (`industry, emotion, fit, rationale`), all 15×7.

**Definition of Done:** generators reproduce identical CSVs re-run (seeded); datasets + artifacts committed; KMeans recovers the 5 personas; goal momentum moves the reforecast +5..+20; **the §F.3 acceptance case reproduces** ($100k food_delivery/push → baseline ROAS ≈ 1.35, M≈1.9 ROAS ≈ 3.7); package imports no fastapi/sqlalchemy.

---

## 6. Integration plan (three gates, no clocks)

| Gate | Pass condition |
|---|---|
| **0 · Foundation** | Saanvi's Phase 0 on `main`; `uvicorn app.main:app` boots and serves stub/seed data. W1 and W3 start immediately after. |
| **1 · Merge** | One workstream at a time into `main`: W1 in ⇒ endpoints serve flowing replay data; W3 in ⇒ stubs flag off, real numbers everywhere. Mismatches are fixed *toward the contract*. |
| **2 · Full loop** | `smoke_test.py` green from cold start: replay → goal moment fires → auto-campaign persists with real Gemini copy + ROI + evidence → reforecast delta visible. **This is "done."** Everything after (YouTube/news connectors, real capture file, richer playbook, then frontend) is stretch, strictly in that order. |

**Rules:** contract is law (changes = human approval + doc + `contracts.py` in one commit + version bump) · never write outside your paths · `requirements.txt`/`.env.example` append-only with announcement · all randomness seeded, artifacts committed · if blocked, stub per the contract and keep moving · when in doubt, choose the simpler design (§0.3).
